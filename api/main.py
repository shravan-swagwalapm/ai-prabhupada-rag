#!/usr/bin/env python3
"""
FastAPI Backend — AI Prabhupada RAG API

Endpoints:
    POST /api/auth/google     — Google Sign-In → JWT
    GET  /api/user            — Current user info + quota
    GET  /api/history         — Paginated question history
    POST /api/waitlist        — Join waitlist for more quota
    POST /api/query           — Ask a question, get scripture results + AI answer + audio
    GET  /api/query/stream    — SSE streaming, word-by-word
    GET  /api/audio/{id}      — Serve generated audio files
    GET  /api/audio/{id}/status — Poll audio status
    GET  /api/health          — Health check

Start:
    cd ~/ai-prabhupada-rag
    uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations

import collections
import json as json_module
import logging
import os
import re
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

import asyncio
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from api.auth import verify_google_token, create_jwt
from api.circuit_breaker import CircuitBreaker
from api.database import (
    init_db, upsert_user, get_user, get_quota, decrement_quota,
    save_question, get_history, save_waitlist,
)
from api.middleware import get_current_user
from api.models import (
    GoogleAuthRequest, AuthResponse, UserInfo,
    HistoryEntry, HistoryResponse, WaitlistRequest,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("api.main")

# ── Paths & startup ───────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

AUDIO_CACHE_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data_local"))) / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.50"))

# ── Global search function (loaded once) ─────────────────────────────────────
_search_func = None
_search_with_embedding_func = None
_faiss_loaded = False

# ── Semantic answer cache ────────────────────────────────────────────────────
_answer_cache = None

# ── Circuit breaker for ElevenLabs ───────────────────────────────────────────
_elevenlabs_breaker = CircuitBreaker()

# ── Audio job registry (bounded to prevent unbounded memory growth) ───────────
_audio_jobs: Dict[str, str] = {}   # audio_id -> "pending" | "ready" | "error" | "unavailable"
_MAX_AUDIO_JOBS = 500              # Evict oldest entries when this is exceeded
_audio_jobs_lock = threading.Lock()

# ── Rate limiting (simple sliding-window, per client IP) ─────────────────────
_RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
_RATE_LIMIT_WINDOW_SECS = int(os.getenv("RATE_LIMIT_WINDOW_SECS", "60"))
_rate_limit_store: Dict[str, collections.deque] = {}
_rate_limit_lock = threading.Lock()

# ── CORS ──────────────────────────────────────────────────────────────────────
_default_origins = "http://localhost:3000,http://localhost:3001,http://localhost:8000"
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if o.strip()
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _store_audio_job(audio_id: str, status: str) -> None:
    """Store an audio job, evicting the oldest entry if at capacity."""
    with _audio_jobs_lock:
        if len(_audio_jobs) >= _MAX_AUDIO_JOBS:
            oldest_key = next(iter(_audio_jobs))
            del _audio_jobs[oldest_key]
            logger.debug("Evicted oldest audio job to stay under limit")
        _audio_jobs[audio_id] = status


def _update_audio_job(audio_id: str, status: str) -> None:
    with _audio_jobs_lock:
        _audio_jobs[audio_id] = status


def _get_audio_job(audio_id: str) -> Optional[str]:
    with _audio_jobs_lock:
        return _audio_jobs.get(audio_id)


def _is_rate_limited(client_ip: str) -> bool:
    """Return True if the client IP has exceeded the rate limit."""
    now = time.monotonic()
    with _rate_limit_lock:
        if client_ip not in _rate_limit_store:
            _rate_limit_store[client_ip] = collections.deque()

        window = _rate_limit_store[client_ip]
        while window and now - window[0] > _RATE_LIMIT_WINDOW_SECS:
            window.popleft()

        if len(window) >= _RATE_LIMIT_REQUESTS:
            return True

        window.append(now)

        if len(_rate_limit_store) > 5000:
            stale = [
                k for k, v in _rate_limit_store.items()
                if not v or now - v[-1] > _RATE_LIMIT_WINDOW_SECS * 2
            ]
            for k in stale[:2500]:
                del _rate_limit_store[k]

        return False


def load_search() -> None:
    """Load FAISS search function (called once at startup)."""
    global _search_func, _search_with_embedding_func, _faiss_loaded
    try:
        from search_scriptures_faiss import search_scriptures_faiss as sf
        from search_scriptures_faiss import search_with_embedding as swe
        _search_func = sf
        _search_with_embedding_func = swe
        _faiss_loaded = True
        logger.info("FAISS index loaded successfully at startup")
    except Exception as e:
        logger.warning("FAISS not available (%s), falling back to brute-force", e)
        try:
            from search_scriptures import search_scriptures_cached as sf
            _search_func = sf
            _faiss_loaded = False
        except Exception as e2:
            logger.error("Could not load any search backend: %s", e2)
            _search_func = None
            _faiss_loaded = False


def _init_answer_cache() -> None:
    """Initialize the semantic answer cache at startup."""
    global _answer_cache
    try:
        from api.answer_cache import SemanticAnswerCache
        _answer_cache = SemanticAnswerCache()
        _answer_cache.load()
        logger.info("Semantic answer cache initialized (%d entries)", _answer_cache.size())
    except Exception as e:
        logger.warning("Failed to initialize answer cache: %s", e)
        _answer_cache = None


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    load_search()
    _init_answer_cache()
    yield
    logger.info("API server shutting down")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Prabhupada RAG API",
    description=(
        "Spiritual question-answering powered by FAISS search, "
        "Claude Sonnet 4.5, and Prabhupada's voice"
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)


# ── Rate-limiting middleware ───────────────────────────────────────────────────

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to expensive query endpoints."""
    if request.url.path in ("/api/query", "/api/query/stream"):
        client_ip = (request.client.host if request.client else "unknown")
        if _is_rate_limited(client_ip):
            logger.warning("Rate limit hit for IP %s on %s", client_ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": (
                        f"Maximum {_RATE_LIMIT_REQUESTS} requests per "
                        f"{_RATE_LIMIT_WINDOW_SECS}s. Please wait."
                    ),
                },
            )
    return await call_next(request)


# ── Request / Response models ─────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    include_ai: bool = True
    include_voice: bool = False

    @field_validator("question")
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        return v.strip()


class PassageResult(BaseModel):
    scripture: str
    text: str
    similarity: float
    chunk_id: str = ""


class QueryResponse(BaseModel):
    question: str
    passages: List[PassageResult]
    ai_answer: Optional[str] = None
    audio_id: Optional[str] = None
    search_method: str = ""
    cached: bool = False
    message: Optional[str] = None


# ── Audio background task ─────────────────────────────────────────────────────

def generate_audio_background(audio_id: str, text: str) -> None:
    """Background task: generate voice audio with circuit breaker protection."""
    # Check circuit breaker before attempting synthesis
    if _elevenlabs_breaker.is_open():
        logger.warning("ElevenLabs circuit breaker is OPEN, skipping audio %s", audio_id)
        _update_audio_job(audio_id, "unavailable")
        return

    try:
        from voice_synthesizer import synthesize_speech
        output_path = AUDIO_CACHE_DIR / f"{audio_id}.mp3"
        synthesize_speech(text, output_path=output_path)
        _update_audio_job(audio_id, "ready")
        _elevenlabs_breaker.record_success()
        logger.info("Audio ready: %s", audio_id)
    except FileNotFoundError as e:
        logger.warning("Voice not configured: %s", e)
        _update_audio_job(audio_id, "error")
    except Exception as e:
        logger.error("Audio generation failed for %s: %s", audio_id, e, exc_info=True)
        _elevenlabs_breaker.record_failure()
        _update_audio_job(audio_id, "error")


# ── Auth Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/auth/google", response_model=AuthResponse)
async def auth_google(req: GoogleAuthRequest):
    """Verify Google ID token, create/update user, return JWT + user info."""
    google_info = verify_google_token(req.id_token)

    user_id = upsert_user(
        google_id=google_info["sub"],
        email=google_info["email"],
        name=google_info["name"],
        photo_url=google_info.get("picture"),
    )

    token = create_jwt(user_id, google_info["email"])
    user = get_user(user_id)

    return AuthResponse(
        token=token,
        user=UserInfo(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            photo_url=user.get("photo_url"),
            text_quota=user["text_quota"],
            voice_quota=user["voice_quota"],
        ),
    )


@app.get("/api/user", response_model=UserInfo)
async def get_current_user_info(user_id: str = Depends(get_current_user)):
    """Get current user info with fresh quota counts."""
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserInfo(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        photo_url=user.get("photo_url"),
        text_quota=user["text_quota"],
        voice_quota=user["voice_quota"],
    )


@app.get("/api/history", response_model=HistoryResponse)
async def get_user_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user),
):
    """Get paginated question history for the current user."""
    result = get_history(user_id, limit=limit, offset=offset)

    entries = [
        HistoryEntry(
            id=e["id"],
            question=e["question"],
            answer_text=e["answer_text"],
            answer_mode=e["answer_mode"],
            audio_id=e.get("audio_id"),
            created_at=e["created_at"],
        )
        for e in result["entries"]
    ]

    return HistoryResponse(entries=entries, total=result["total"])


@app.post("/api/waitlist")
async def join_waitlist(
    req: WaitlistRequest,
    user_id: str = Depends(get_current_user),
):
    """Add email to waitlist for more quota."""
    save_waitlist(req.email, user_id=user_id)
    return {"status": "ok"}


# ── Query Endpoints (with auth + quota) ──────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check. Returns HTTP 503 when search backend is not ready."""
    ready = _search_func is not None
    body = {
        "status": "ok" if ready else "degraded",
        "faiss_loaded": _faiss_loaded,
        "search_ready": ready,
        "cache_entries": _answer_cache.size() if _answer_cache else 0,
    }
    if not ready:
        return JSONResponse(status_code=503, content=body)
    return body


@app.post("/api/query", response_model=QueryResponse)
async def query_scriptures(
    req: QueryRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
):
    """
    Main query endpoint with auth + quota enforcement.

    1. Check quota
    2. Check semantic cache
    3. FAISS search for scripture passages
    4. Claude Sonnet 4.5 generates answer
    5. ElevenLabs voice synthesis in background
    6. Decrement quota + save to history
    """
    if _search_func is None:
        raise HTTPException(status_code=503, detail="Search backend not ready")

    # Quota check
    mode = "voice" if req.include_voice else "text"
    quota = get_quota(user_id)
    quota_key = f"{mode}_quota"
    if quota[quota_key] <= 0:
        return JSONResponse(
            status_code=402,
            content={
                "detail": f"Your {mode} quota is exhausted",
                "quota_type": mode,
                "remaining": 0,
            },
        )

    logger.info(
        "POST /api/query user=%s question='%s...' top_k=%d voice=%s",
        user_id[:8], req.question[:60], req.top_k, req.include_voice,
    )

    # Try semantic cache first (if embedding search available)
    if _answer_cache and _search_with_embedding_func:
        try:
            raw_results, embedding = _search_with_embedding_func(req.question, top_k=req.top_k)
            cached = _answer_cache.lookup(embedding, mode)
            if cached:
                logger.info("Cache HIT for query: '%s...'", req.question[:40])
                passages = [
                    PassageResult(
                        scripture=r.get("scripture", ""),
                        text=r.get("text", ""),
                        similarity=r.get("similarity", 0.0),
                        chunk_id=str(r.get("chunk_id", "")),
                    )
                    for r in raw_results
                ]
                decrement_quota(user_id, mode)
                save_question(user_id, req.question, cached["answer_text"], mode,
                              cached.get("audio_id"), cached.get("passages_json", "[]"))
                return QueryResponse(
                    question=req.question,
                    passages=passages,
                    ai_answer=cached["answer_text"],
                    audio_id=cached.get("audio_id"),
                    search_method="faiss",
                    cached=True,
                )
        except Exception as e:
            logger.warning("Cache/embedding search failed, falling back: %s", e)
            raw_results = None
            embedding = None
    else:
        raw_results = None
        embedding = None

    # Standard FAISS search (if not already done via search_with_embedding)
    if raw_results is None:
        try:
            raw_results = list(_search_func(req.question, top_k=req.top_k))
        except Exception as e:
            logger.error("Search failed: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    passages = [
        PassageResult(
            scripture=r.get("scripture", ""),
            text=r.get("text", ""),
            similarity=r.get("similarity", 0.0),
            chunk_id=str(r.get("chunk_id", "")),
        )
        for r in raw_results
    ]

    # Relevance floor — return early if no passage meets MIN_RELEVANCE_SCORE
    relevant_results = [r for r in raw_results if r.get("similarity", 0) >= MIN_RELEVANCE_SCORE]
    if not relevant_results:
        return QueryResponse(
            question=req.question,
            passages=passages,
            ai_answer=None,
            audio_id=None,
            search_method="faiss" if _faiss_loaded else "brute_force",
            message="I could not find a direct teaching on this topic. Try rephrasing with specific scripture terms.",
        )

    ai_answer: Optional[str] = None
    audio_id: Optional[str] = None

    # AI answer
    if req.include_ai and relevant_results:
        try:
            from generate_answer import generate_answer
            answer_mode = "concise" if req.include_voice else "full"
            ai_answer = generate_answer(req.question, relevant_results, mode=answer_mode)
        except Exception as e:
            logger.error("Answer generation failed: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Answer generation failed: {e}")

    # Voice synthesis (background)
    if req.include_voice and ai_answer:
        audio_id = str(uuid.uuid4())[:8]
        _store_audio_job(audio_id, "pending")
        background_tasks.add_task(generate_audio_background, audio_id, ai_answer)

    # Decrement quota + save history
    if ai_answer:
        decrement_quota(user_id, mode)
        passages_json = json_module.dumps([{"scripture": r.get("scripture", ""), "text": r.get("text", "")[:200]} for r in relevant_results])
        save_question(user_id, req.question, ai_answer, mode, audio_id, passages_json)

        # Store in semantic cache
        if _answer_cache and embedding is not None:
            try:
                _answer_cache.store(embedding, req.question, ai_answer, audio_id, mode, passages_json)
            except Exception as e:
                logger.warning("Failed to store in cache: %s", e)

    return QueryResponse(
        question=req.question,
        passages=passages,
        ai_answer=ai_answer,
        audio_id=audio_id,
        search_method="faiss" if _faiss_loaded else "brute_force",
    )


@app.get("/api/query/stream")
async def query_stream(
    request: Request,
    question: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(default=5, ge=1, le=20),
    include_voice: bool = Query(default=False),
    user_id: str = Depends(get_current_user),
):
    """
    Streaming endpoint with auth + quota + semantic cache.
    Streams AI answer word-by-word via SSE.
    """
    if _search_func is None:
        raise HTTPException(status_code=503, detail="Search backend not ready")

    question = question.strip()
    mode = "voice" if include_voice else "text"

    # Quota check (before streaming)
    quota = get_quota(user_id)
    quota_key = f"{mode}_quota"
    if quota[quota_key] <= 0:
        return JSONResponse(
            status_code=402,
            content={
                "detail": f"Your {mode} quota is exhausted",
                "quota_type": mode,
                "remaining": 0,
            },
        )

    logger.info(
        "GET /api/query/stream user=%s question='%s...' top_k=%d voice=%s",
        user_id[:8], question[:60], top_k, include_voice,
    )

    async def event_stream():
        nonlocal question, mode

        # Step 1: FAISS search (with embedding for cache)
        raw_results = None
        embedding = None

        if _search_with_embedding_func:
            try:
                raw_results, embedding = _search_with_embedding_func(question, top_k=top_k)
            except Exception as e:
                logger.warning("Embedding search failed: %s", e)

        if raw_results is None:
            try:
                raw_results = list(_search_func(question, top_k=top_k))
            except Exception as e:
                logger.error("Search failed in stream: %s", e)
                yield f"data: {json_module.dumps({'type': 'error', 'message': 'Search failed'})}\n\n"
                return

        passages = [
            {
                "scripture": r.get("scripture", ""),
                "text": r.get("text", ""),
                "similarity": r.get("similarity", 0.0),
            }
            for r in raw_results
        ]
        yield f"data: {json_module.dumps({'type': 'passages', 'data': passages})}\n\n"

        # Relevance floor — skip answer if no passage meets MIN_RELEVANCE_SCORE
        relevant_results = [r for r in raw_results if r.get("similarity", 0) >= MIN_RELEVANCE_SCORE]
        if not relevant_results:
            yield f"data: {json_module.dumps({'type': 'no_match', 'message': 'I could not find a direct teaching on this topic. Try rephrasing with specific scripture terms.'})}\n\n"
            yield f"data: {json_module.dumps({'type': 'done'})}\n\n"
            return

        # Step 2: Check semantic cache
        if _answer_cache and embedding is not None:
            cached = _answer_cache.lookup(embedding, mode)
            if cached:
                logger.info("Stream cache HIT for: '%s...'", question[:40])
                # Emit cached answer as sentence chunks with small delays (preserves UX)
                cached_text = cached["answer_text"]
                import re as re_mod
                sentences = re_mod.split(r'(?<=[.!?])\s+', cached_text)
                for sentence in sentences:
                    if sentence.strip():
                        yield f"data: {json_module.dumps({'type': 'answer_chunk', 'data': sentence + ' '})}\n\n"
                        await asyncio.sleep(0.02)

                # Voice: return existing audio_id if available
                if include_voice and cached.get("audio_id"):
                    yield f"data: {json_module.dumps({'type': 'audio_id', 'data': cached['audio_id']})}\n\n"

                # Decrement quota + save history
                decrement_quota(user_id, mode)
                save_question(user_id, question, cached_text, mode,
                              cached.get("audio_id"), cached.get("passages_json", "[]"))

                yield f"data: {json_module.dumps({'type': 'done', 'cached': True})}\n\n"
                return

        # Step 3: Stream fresh AI answer
        full_answer: List[str] = []
        answer_mode = "concise" if include_voice else "full"

        if relevant_results:
            try:
                from generate_answer import generate_answer_streaming
                for chunk in generate_answer_streaming(question, relevant_results, mode=answer_mode):
                    full_answer.append(chunk)
                    yield f"data: {json_module.dumps({'type': 'answer_chunk', 'data': chunk})}\n\n"
                    await asyncio.sleep(0)
            except Exception as e:
                logger.error("Streaming generation failed: %s", e)
                yield f"data: {json_module.dumps({'type': 'error', 'message': 'Answer generation failed'})}\n\n"

        # Step 4: Voice synthesis (background, with circuit breaker)
        audio_id = None
        if include_voice and full_answer:
            answer_text = "".join(full_answer)
            audio_id = str(uuid.uuid4())[:8]

            if _elevenlabs_breaker.is_open():
                _store_audio_job(audio_id, "unavailable")
                yield f"data: {json_module.dumps({'type': 'audio_status', 'data': 'unavailable'})}\n\n"
            else:
                _store_audio_job(audio_id, "pending")
                t = threading.Thread(
                    target=generate_audio_background,
                    args=(audio_id, answer_text),
                    daemon=True,
                    name=f"voice-{audio_id}",
                )
                t.start()
                yield f"data: {json_module.dumps({'type': 'audio_id', 'data': audio_id})}\n\n"

        # Step 5: Decrement quota + save to history + cache
        if full_answer:
            answer_text = "".join(full_answer)
            decrement_quota(user_id, mode)
            passages_json = json_module.dumps([
                {"scripture": r.get("scripture", ""), "text": r.get("text", "")[:200]}
                for r in raw_results
            ])
            save_question(user_id, question, answer_text, mode, audio_id, passages_json)

            # Store in semantic cache
            if _answer_cache and embedding is not None:
                try:
                    _answer_cache.store(embedding, question, answer_text, audio_id, mode, passages_json)
                except Exception as e:
                    logger.warning("Failed to store in cache: %s", e)

        yield f"data: {json_module.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Audio Endpoints ──────────────────────────────────────────────────────────

@app.get("/api/audio/{audio_id}")
async def get_audio(audio_id: str):
    """Serve a generated audio file."""
    if not re.fullmatch(r"[a-zA-Z0-9\-]{1,64}", audio_id):
        raise HTTPException(status_code=400, detail="Invalid audio ID format")

    status = _get_audio_job(audio_id)

    if status is None:
        raise HTTPException(status_code=404, detail="Audio ID not found")

    if status == "pending":
        return JSONResponse(
            status_code=202,
            content={"status": "pending", "message": "Audio is being generated..."},
        )

    if status == "unavailable":
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "message": "Voice temporarily unavailable"},
        )

    if status == "error":
        raise HTTPException(status_code=500, detail="Audio generation failed")

    audio_path = AUDIO_CACHE_DIR / f"{audio_id}.mp3"
    if not audio_path.exists():
        logger.error("Audio file missing despite ready status: %s", audio_path)
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=f"prabhupada_{audio_id}.mp3",
    )


@app.get("/api/audio/{audio_id}/status")
async def audio_status(audio_id: str):
    """Check audio generation status."""
    if not re.fullmatch(r"[a-zA-Z0-9\-]{1,64}", audio_id):
        raise HTTPException(status_code=400, detail="Invalid audio ID format")

    status = _get_audio_job(audio_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Audio ID not found")

    return {"audio_id": audio_id, "status": status}


# ---------------------------------------------------------------------------
# Static frontend serving (MUST be LAST — catches all non-API routes)
# ---------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles

_frontend_dir = PROJECT_ROOT / "web" / "out"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
    logger.info("Serving frontend from %s", _frontend_dir)
