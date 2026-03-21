#!/usr/bin/env python3
"""
FAISS-accelerated scripture search (Phase 3 Part 2)
Expected: 50-100x faster than brute-force
Query time: 10s → 0.1-0.2s
"""
import json
import logging
import threading
import time
import os
from pathlib import Path
from typing import List, Dict, Optional
from functools import lru_cache
from dotenv import load_dotenv
import numpy as np
import faiss
import requests

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent

# Support DATA_DIR (Railway persistent volume) or fallback to project root
_data_dir = os.getenv("DATA_DIR")
if _data_dir and (Path(_data_dir) / "faiss_indexes" / "scripture_ivf100.index").exists():
    INDEX_DIR = Path(_data_dir) / "faiss_indexes"
else:
    INDEX_DIR = PROJECT_ROOT / "faiss_indexes"
INDEX_FILE = INDEX_DIR / "scripture_ivf100.index"
METADATA_FILE = INDEX_DIR / "metadata.json"

# Voyage AI configuration
VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
EMBEDDING_MODEL = "voyage-3-large"
VOYAGE_REQUEST_TIMEOUT = 30  # seconds — fail fast rather than hang
VOYAGE_MAX_RETRIES = 3

# Query validation
MAX_QUERY_LENGTH = 1000
MAX_TOP_K = 50

# Thread-safe global state — prevents double-loading under concurrent requests
_INDEX = None
_METADATA = None
_LOADED = False
_LOAD_LOCK = threading.Lock()


def _get_voyage_api_key() -> str:
    """Get and validate Voyage API key lazily (not at import time)."""
    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        raise ValueError(
            "VOYAGE_API_KEY not found in environment variables. "
            "Add it to your .env file."
        )
    return api_key


VECTORS_FILE = INDEX_DIR / "vectors.npy"


def _build_index_from_vectors(vectors: np.ndarray, nlist: int = 100) -> faiss.Index:
    """Build FAISS IVF index from raw numpy vectors (portable across platforms)."""
    n, d = vectors.shape
    logger.info("Building FAISS IVF%d index from %d vectors (%dD)...", nlist, n, d)
    start = time.time()
    quantizer = faiss.IndexFlatIP(d)
    index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)
    index.train(vectors)
    index.add(vectors)
    index.nprobe = 10
    elapsed = time.time() - start
    logger.info("Built FAISS index in %.2fs", elapsed)
    return index


def load_faiss_index():
    """Load FAISS index once with double-checked locking for thread safety.

    Tries faiss.read_index first (fast). If that fails (cross-platform binary
    incompatibility), rebuilds from vectors.npy (portable numpy format, ~1s).
    """
    global _INDEX, _METADATA, _LOADED

    # Fast path — no lock needed once loaded
    if _LOADED:
        return _INDEX, _METADATA

    with _LOAD_LOCK:
        # Double-checked locking: re-check after acquiring lock
        if _LOADED:
            return _INDEX, _METADATA

        if not METADATA_FILE.exists():
            logger.error("FAISS metadata not found at %s", METADATA_FILE)
            return None, None

        start = time.time()

        # Try loading pre-built index first (fastest path)
        if INDEX_FILE.exists():
            try:
                logger.info("Loading FAISS index from %s...", INDEX_FILE)
                _INDEX = faiss.read_index(str(INDEX_FILE))
                _INDEX.nprobe = 10
            except Exception as e:
                logger.warning("Pre-built FAISS index failed: %s", e)
                _INDEX = None

        # Fallback: rebuild from portable vectors.npy
        if _INDEX is None and VECTORS_FILE.exists():
            try:
                logger.info("Rebuilding FAISS index from %s...", VECTORS_FILE)
                vectors = np.load(str(VECTORS_FILE))
                _INDEX = _build_index_from_vectors(vectors)
            except Exception as e:
                logger.error("Failed to rebuild FAISS index: %s", e, exc_info=True)
                _INDEX = None
                _METADATA = None
                return None, None

        if _INDEX is None:
            logger.error(
                "No FAISS index or vectors.npy found in %s. "
                "Run: python3 scripts/build_faiss_index.py",
                INDEX_DIR,
            )
            return None, None

        # Load metadata
        try:
            with open(METADATA_FILE) as f:
                _METADATA = json.load(f)
        except Exception as e:
            logger.error("Failed to load metadata: %s", e)
            _INDEX = None
            _METADATA = None
            return None, None

        elapsed = time.time() - start
        logger.info("Loaded %d vectors in %.2fs", _INDEX.ntotal, elapsed)
        _LOADED = True

    return _INDEX, _METADATA


def create_embedding(text: str) -> list:
    """Create embedding with cache and exponential-backoff retry on failure."""
    # Import embedding cache (Phase 2 reuse)
    import sys
    if str(PROJECT_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from embedding_cache import get_cache

    cache = get_cache()
    cached = cache.get(text)

    if cached:
        logger.debug("Embedding cache hit")
        return cached

    logger.debug("Calling Voyage AI API for embedding")
    api_key = _get_voyage_api_key()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {"input": [text], "model": EMBEDDING_MODEL}

    last_error: Exception = RuntimeError("No attempts made")
    for attempt in range(VOYAGE_MAX_RETRIES):
        try:
            response = requests.post(
                VOYAGE_API_URL,
                headers=headers,
                json=payload,
                timeout=VOYAGE_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            embedding = response.json()["data"][0]["embedding"]
            cache.set(text, embedding)
            logger.debug("Embedding created and cached")
            return embedding

        except requests.exceptions.Timeout:
            last_error = TimeoutError(
                f"Voyage AI API timed out after {VOYAGE_REQUEST_TIMEOUT}s"
            )
            logger.warning(
                "Attempt %d/%d: Voyage AI timeout", attempt + 1, VOYAGE_MAX_RETRIES
            )
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                wait = 2 ** attempt
                logger.warning(
                    "Voyage AI rate limited, retrying in %ds (attempt %d/%d)",
                    wait, attempt + 1, VOYAGE_MAX_RETRIES,
                )
                time.sleep(wait)
                last_error = e
                continue
            # Non-retriable HTTP error
            logger.error("Voyage AI HTTP error %s: %s", e.response.status_code if e.response else "?", e)
            raise
        except Exception as e:
            last_error = e
            logger.warning("Attempt %d/%d failed: %s", attempt + 1, VOYAGE_MAX_RETRIES, e)

        if attempt < VOYAGE_MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    raise RuntimeError(
        f"Failed to create embedding after {VOYAGE_MAX_RETRIES} attempts: {last_error}"
    ) from last_error


def search_scriptures_faiss(
    query: str,
    top_k: int = 5,
    scripture_filter: Optional[str] = None,
) -> List[Dict]:
    """
    FAISS-accelerated search (Phase 3 Part 2).
    Expected: 50-100x faster than brute-force (10s → 0.1-0.2s).

    Raises:
        ValueError: For invalid inputs.
        RuntimeError: If the FAISS index is not loaded or embedding fails.
    """
    # Input validation
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query too long: {len(query)} chars (max {MAX_QUERY_LENGTH})")
    if not isinstance(top_k, int) or top_k < 1 or top_k > MAX_TOP_K:
        raise ValueError(f"top_k must be an integer between 1 and {MAX_TOP_K}")

    query = query.strip()
    logger.info("FAISS search: '%s...' top_k=%d", query[:80], top_k)

    index, metadata = load_faiss_index()

    if index is None or metadata is None:
        logger.error("FAISS index not loaded — cannot search")
        return []

    # Create and normalize query embedding
    query_embedding = create_embedding(query)
    query_vector = np.array([query_embedding], dtype=np.float32)
    faiss.normalize_L2(query_vector)

    # FAISS search
    start = time.time()
    search_k = top_k * 10 if scripture_filter else top_k
    similarities, indices = index.search(query_vector, search_k)
    search_time = time.time() - start

    logger.debug("FAISS search: %.1fms (%d candidates)", search_time * 1000, search_k)

    # Build results
    results = []
    for sim, idx in zip(similarities[0], indices[0]):
        if idx == -1:  # FAISS returns -1 for empty slots
            continue

        chunk_meta = metadata[idx]

        # Apply scripture filter if specified
        if scripture_filter and chunk_meta.get("scripture") != scripture_filter:
            continue

        results.append({
            "scripture": chunk_meta.get("scripture", "Unknown"),
            "chunk_id": chunk_meta.get("chunk_id", ""),
            "text": chunk_meta.get("text", ""),
            "similarity": float(sim),
        })

        if len(results) >= top_k:
            break

    logger.info("Returning %d results for query '%s...'", len(results), query[:40])
    return results


def search_with_embedding(
    query: str,
    top_k: int = 5,
    scripture_filter: Optional[str] = None,
) -> tuple:
    """
    Like search_scriptures_faiss() but also returns the normalized query embedding.
    Returns (results: List[Dict], query_vector: np.ndarray of shape (dim,), dtype float32).
    This avoids calling Voyage AI twice when the cache needs the embedding.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query too long: {len(query)} chars (max {MAX_QUERY_LENGTH})")
    if not isinstance(top_k, int) or top_k < 1 or top_k > MAX_TOP_K:
        raise ValueError(f"top_k must be an integer between 1 and {MAX_TOP_K}")

    query = query.strip()
    logger.info("FAISS search (with embedding): '%s...' top_k=%d", query[:80], top_k)

    index, metadata = load_faiss_index()
    if index is None or metadata is None:
        logger.error("FAISS index not loaded — cannot search")
        return [], np.zeros(0, dtype=np.float32)

    # Create and normalize query embedding
    query_embedding = create_embedding(query)
    query_vector = np.array([query_embedding], dtype=np.float32)
    faiss.normalize_L2(query_vector)

    # FAISS search
    start = time.time()
    search_k = top_k * 10 if scripture_filter else top_k
    similarities, indices = index.search(query_vector, search_k)
    search_time = time.time() - start

    logger.debug("FAISS search: %.1fms (%d candidates)", search_time * 1000, search_k)

    results = []
    for sim, idx in zip(similarities[0], indices[0]):
        if idx == -1:
            continue
        chunk_meta = metadata[idx]
        if scripture_filter and chunk_meta.get("scripture") != scripture_filter:
            continue
        results.append({
            "scripture": chunk_meta.get("scripture", "Unknown"),
            "chunk_id": chunk_meta.get("chunk_id", ""),
            "text": chunk_meta.get("text", ""),
            "similarity": float(sim),
        })
        if len(results) >= top_k:
            break

    logger.info("Returning %d results for query '%s...'", len(results), query[:40])
    # Return the normalized vector (shape: (dim,)) alongside results
    return results, query_vector[0]


@lru_cache(maxsize=1000)
def search_scriptures_faiss_cached(
    query: str,
    top_k: int = 5,
    scripture_filter: Optional[str] = None,
) -> tuple:
    """
    Cached version with LRU eviction for repeated queries.
    Returns a tuple of dicts (treat as read-only — mutating cached results
    corrupts the cache).
    """
    results = search_scriptures_faiss(query, top_k, scripture_filter)
    # Shallow-copy each dict so callers get their own instance
    return tuple(dict(r) for r in results)


def main():
    """Interactive search interface with FAISS."""
    logging.basicConfig(
        level=logging.WARNING,  # Keep quiet in interactive mode
        format="%(levelname)s %(name)s: %(message)s",
    )
    print("AI Prabhupada RAG - FAISS Search (Phase 3)")
    print("=" * 50)

    while True:
        try:
            query = input("\n🔍 Enter search query (or 'quit' to exit): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if query.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if not query:
            continue

        try:
            results = list(search_scriptures_faiss_cached(query, top_k=3))
        except Exception as e:
            print(f"Search failed: {e}")
            continue

        if not results:
            print("No results found.")
            continue

        print(f"\nTop {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. [{result['scripture']}] (similarity: {result['similarity']:.3f})")
            print(f"   {result['text'][:200]}...")
            print()


if __name__ == "__main__":
    main()
