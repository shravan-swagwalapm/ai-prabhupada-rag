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
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data_local")))
DB_PATH = DATA_DIR / "prabhupada.db"

# Default quotas for new users
DEFAULT_TEXT_QUOTA = 5
DEFAULT_VOICE_QUOTA = 2


def _get_conn() -> sqlite3.Connection:
    """Get a thread-local SQLite connection with WAL mode."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    conn = _get_conn()
    try:
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
    finally:
        conn.close()


def upsert_user(google_id: str, email: str, name: str, photo_url: Optional[str]) -> str:
    """Create or update a user by google_id. Returns user id."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE google_id = ?", (google_id,)
        ).fetchone()

        if row:
            # Update existing user info (name/photo may change)
            conn.execute(
                "UPDATE users SET email = ?, name = ?, photo_url = ? WHERE google_id = ?",
                (email, name, photo_url, google_id),
            )
            conn.commit()
            return row["id"]

        # New user
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn.execute(
            """INSERT INTO users (id, google_id, email, name, photo_url, text_quota, voice_quota, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, google_id, email, name, photo_url,
             DEFAULT_TEXT_QUOTA, DEFAULT_VOICE_QUOTA, now),
        )
        conn.commit()
        logger.info("New user created: %s (%s)", name, email)
        return user_id
    finally:
        conn.close()


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by id. Returns dict or None."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_quota(user_id: str) -> Dict[str, int]:
    """Get remaining quota for a user."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT text_quota, voice_quota FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return {"text_quota": 0, "voice_quota": 0}
        return {"text_quota": row["text_quota"], "voice_quota": row["voice_quota"]}
    finally:
        conn.close()


def decrement_quota(user_id: str, mode: str) -> bool:
    """Decrement quota for a mode ('text' or 'voice'). Returns True if successful."""
    col = "text_quota" if mode == "text" else "voice_quota"
    conn = _get_conn()
    try:
        result = conn.execute(
            f"UPDATE users SET {col} = {col} - 1 WHERE id = ? AND {col} > 0",
            (user_id,),
        )
        conn.commit()
        return result.rowcount > 0
    finally:
        conn.close()


def save_question(
    user_id: str,
    question: str,
    answer_text: str,
    mode: str,
    audio_id: Optional[str],
    passages_json: str,
) -> str:
    """Save a Q&A to history. Returns question id."""
    conn = _get_conn()
    try:
        qid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn.execute(
            """INSERT INTO questions (id, user_id, question, answer_text, answer_mode, audio_id, passages_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (qid, user_id, question, answer_text, mode, audio_id, passages_json, now),
        )
        conn.commit()
        return qid
    finally:
        conn.close()


def get_history(user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Get paginated question history for a user."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT id, question, answer_text, answer_mode, audio_id, created_at
               FROM questions WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        ).fetchall()

        total_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM questions WHERE user_id = ?", (user_id,)
        ).fetchone()

        entries = [dict(r) for r in rows]
        return {"entries": entries, "total": total_row["cnt"]}
    finally:
        conn.close()


def save_waitlist(email: str, user_id: Optional[str] = None) -> str:
    """Add email to waitlist. Returns waitlist entry id."""
    conn = _get_conn()
    try:
        wid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO waitlist (id, email, user_id, created_at) VALUES (?, ?, ?, ?)",
            (wid, email, user_id, now),
        )
        conn.commit()
        return wid
    finally:
        conn.close()


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
    conn = _get_conn()
    try:
        cid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conn.execute(
            """INSERT INTO answer_cache
               (id, question, answer_text, audio_id, mode, passages_json, embedding_blob, created_at, last_used_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cid, question, answer_text, audio_id, mode, passages_json, embedding_blob, now, now),
        )
        conn.commit()
        return cid
    finally:
        conn.close()


def get_all_cache_entries() -> List[Dict[str, Any]]:
    """Load all cache entries (for populating in-memory cache at startup)."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, question, answer_text, audio_id, mode, passages_json, embedding_blob, last_used_at FROM answer_cache ORDER BY last_used_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_cache_last_used(cache_id: str) -> None:
    """Update last_used_at for LRU tracking."""
    conn = _get_conn()
    try:
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE answer_cache SET last_used_at = ? WHERE id = ?", (now, cache_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_cache_entry(cache_id: str) -> None:
    """Delete a cache entry (for LRU eviction)."""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM answer_cache WHERE id = ?", (cache_id,))
        conn.commit()
    finally:
        conn.close()


def get_cache_count() -> int:
    """Get current number of cache entries."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM answer_cache").fetchone()
        return row["cnt"]
    finally:
        conn.close()
