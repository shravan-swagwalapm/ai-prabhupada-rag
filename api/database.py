#!/usr/bin/env python3
"""
SQLite database module — AI Prabhupada RAG

Tables: users, questions, answer_cache, waitlist
WAL mode for concurrent reads during writes.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data_local")))
DB_PATH = DATA_DIR / "prabhupada.db"

# Default quotas for new users
DEFAULT_TEXT_QUOTA = 5
DEFAULT_VOICE_QUOTA = 2

# Thread-local storage for connection reuse
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Get a thread-local SQLite connection with WAL mode.
    Reuses the same connection per thread to avoid lock contention."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.execute("SELECT 1")
            return conn
        except sqlite3.ProgrammingError:
            _local.conn = None

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    _local.conn = conn
    return conn


@contextmanager
def _db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database operations. Reuses thread-local connection."""
    yield _get_conn()


def _utcnow() -> str:
    """UTC timestamp as ISO string (timezone-aware, avoids deprecated utcnow)."""
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    """Create all tables if they don't exist."""
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                google_id TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                name TEXT NOT NULL,
                photo_url TEXT,
                text_quota INTEGER NOT NULL DEFAULT 5,
                voice_quota INTEGER NOT NULL DEFAULT 2,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                answer_mode TEXT NOT NULL,
                audio_id TEXT,
                passages_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS answer_cache (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                audio_id TEXT,
                mode TEXT NOT NULL,
                passages_json TEXT,
                embedding_blob BLOB NOT NULL,
                created_at TEXT NOT NULL,
                last_used_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS waitlist (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                user_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_questions_user_id ON questions(user_id);
            CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at);
            CREATE INDEX IF NOT EXISTS idx_answer_cache_mode ON answer_cache(mode);
            CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist(email);
        """)
        conn.commit()
        logger.info("Database initialized at %s", DB_PATH)


def upsert_user(google_id: str, email: str, name: str, photo_url: Optional[str]) -> str:
    """Create or update a user by google_id. Returns user id."""
    with _db() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE google_id = ?", (google_id,)
        ).fetchone()

        if row:
            conn.execute(
                "UPDATE users SET email = ?, name = ?, photo_url = ? WHERE google_id = ?",
                (email, name, photo_url, google_id),
            )
            conn.commit()
            return row["id"]

        user_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO users (id, google_id, email, name, photo_url, text_quota, voice_quota, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, google_id, email, name, photo_url,
             DEFAULT_TEXT_QUOTA, DEFAULT_VOICE_QUOTA, _utcnow()),
        )
        conn.commit()
        logger.info("New user created: %s (%s)", name, email)
        return user_id


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by id. Returns dict or None."""
    with _db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_quota(user_id: str) -> Dict[str, int]:
    """Get remaining quota for a user."""
    with _db() as conn:
        row = conn.execute(
            "SELECT text_quota, voice_quota FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return {"text_quota": 0, "voice_quota": 0}
        return {"text_quota": row["text_quota"], "voice_quota": row["voice_quota"]}


def decrement_quota(user_id: str, mode: str) -> bool:
    """Decrement quota for a mode ('text' or 'voice'). Returns True if successful."""
    if mode not in ("text", "voice"):
        raise ValueError(f"Invalid quota mode: {mode!r}")
    col = "text_quota" if mode == "text" else "voice_quota"
    with _db() as conn:
        result = conn.execute(
            f"UPDATE users SET {col} = {col} - 1 WHERE id = ? AND {col} > 0",
            (user_id,),
        )
        conn.commit()
        return result.rowcount > 0


def refund_quota(user_id: str, mode: str) -> None:
    """Refund one quota unit (e.g., when a query fails after atomic decrement)."""
    if mode not in ("text", "voice"):
        raise ValueError(f"Invalid quota mode: {mode!r}")
    col = "text_quota" if mode == "text" else "voice_quota"
    with _db() as conn:
        conn.execute(f"UPDATE users SET {col} = {col} + 1 WHERE id = ?", (user_id,))
        conn.commit()


def reset_quota(email: str, text_quota: int = DEFAULT_TEXT_QUOTA, voice_quota: int = DEFAULT_VOICE_QUOTA) -> bool:
    """Reset quota for a user by email. Returns True if user was found and updated."""
    with _db() as conn:
        result = conn.execute(
            "UPDATE users SET text_quota = ?, voice_quota = ? WHERE email = ?",
            (text_quota, voice_quota, email),
        )
        conn.commit()
        return result.rowcount > 0


def save_question(
    user_id: str,
    question: str,
    answer_text: str,
    mode: str,
    audio_id: Optional[str],
    passages_json: str,
) -> str:
    """Save a Q&A to history. Returns question id."""
    with _db() as conn:
        qid = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO questions (id, user_id, question, answer_text, answer_mode, audio_id, passages_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (qid, user_id, question, answer_text, mode, audio_id, passages_json, _utcnow()),
        )
        conn.commit()
        return qid


def get_history(user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Get paginated question history for a user."""
    with _db() as conn:
        rows = conn.execute(
            """SELECT id, question, answer_text, answer_mode, audio_id, passages_json, created_at
               FROM questions WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        ).fetchall()

        total_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM questions WHERE user_id = ?", (user_id,)
        ).fetchone()

        entries = [dict(r) for r in rows]
        return {"entries": entries, "total": total_row["cnt"]}


def find_cached_answer(user_id: str, question: str) -> Optional[Dict[str, Any]]:
    """
    Check if the user has already asked this exact question (case-insensitive).
    Returns the most recent matching answer or None.
    """
    normalized = question.strip().lower()
    with _db() as conn:
        row = conn.execute(
            """SELECT answer_text, answer_mode, audio_id, passages_json
               FROM questions
               WHERE user_id = ? AND LOWER(TRIM(question)) = ?
               ORDER BY created_at DESC LIMIT 1""",
            (user_id, normalized),
        ).fetchone()
        return dict(row) if row else None


def save_waitlist(email: str, user_id: Optional[str] = None) -> str:
    """Add email to waitlist. Returns waitlist entry id."""
    with _db() as conn:
        wid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO waitlist (id, email, user_id, created_at) VALUES (?, ?, ?, ?)",
            (wid, email, user_id, _utcnow()),
        )
        conn.commit()
        return wid


# ── Answer Cache CRUD ────────────────────────────────────────────────────────

def save_cache_entry(
    question: str,
    answer_text: str,
    audio_id: Optional[str],
    mode: str,
    passages_json: str,
    embedding_blob: bytes,
) -> str:
    """Save an answer to the semantic cache. Returns cache entry id."""
    with _db() as conn:
        cid = str(uuid.uuid4())
        now = _utcnow()
        conn.execute(
            """INSERT INTO answer_cache
               (id, question, answer_text, audio_id, mode, passages_json, embedding_blob, created_at, last_used_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cid, question, answer_text, audio_id, mode, passages_json, embedding_blob, now, now),
        )
        conn.commit()
        return cid


def get_all_cache_entries() -> List[Dict[str, Any]]:
    """Load all cache entries (for populating in-memory cache at startup)."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, question, answer_text, audio_id, mode, passages_json, embedding_blob, last_used_at FROM answer_cache ORDER BY last_used_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def update_cache_last_used(cache_id: str) -> None:
    """Update last_used_at for LRU tracking."""
    with _db() as conn:
        conn.execute(
            "UPDATE answer_cache SET last_used_at = ? WHERE id = ?", (_utcnow(), cache_id)
        )
        conn.commit()


def delete_cache_entry(cache_id: str) -> None:
    """Delete a cache entry (for LRU eviction)."""
    with _db() as conn:
        conn.execute("DELETE FROM answer_cache WHERE id = ?", (cache_id,))
        conn.commit()


def get_cache_count() -> int:
    """Get current number of cache entries."""
    with _db() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM answer_cache").fetchone()
        return row["cnt"]
