#!/usr/bin/env python3
"""
Semantic Answer Cache — reuse answers for similar questions.

Uses cosine similarity on question embeddings to find cached answers.
Backed by SQLite (persistent) with an in-memory numpy array (fast lookup).
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

import numpy as np

from api.database import (
    delete_cache_entry,
    get_all_cache_entries,
    save_cache_entry,
    update_cache_last_used,
)

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.92
MAX_CACHE_SIZE = 1000


class SemanticAnswerCache:
    """In-memory semantic cache backed by SQLite."""

    def __init__(self) -> None:
        self._embeddings: Optional[np.ndarray] = None  # shape: (n, dim)
        self._entries: list[Dict[str, Any]] = []        # parallel list of metadata
        self._lock = threading.Lock()

    def load(self) -> None:
        """Load all cached entries from SQLite into memory."""
        with self._lock:
            rows = get_all_cache_entries()
            if not rows:
                self._embeddings = None
                self._entries = []
                logger.info("Semantic cache loaded: 0 entries")
                return

            embeddings_list = []
            entries = []
            for row in rows:
                blob = row["embedding_blob"]
                emb = np.frombuffer(blob, dtype=np.float32).copy()
                embeddings_list.append(emb)
                entries.append({
                    "id": row["id"],
                    "question": row["question"],
                    "answer_text": row["answer_text"],
                    "audio_id": row["audio_id"],
                    "mode": row["mode"],
                    "passages_json": row["passages_json"],
                    "last_used_at": row["last_used_at"],
                })

            self._embeddings = np.vstack(embeddings_list)
            self._entries = entries
            logger.info("Semantic cache loaded: %d entries", len(entries))

    def size(self) -> int:
        with self._lock:
            return len(self._entries)

    def lookup(self, question_embedding: np.ndarray, mode: str) -> Optional[Dict[str, Any]]:
        """
        Check if a similar question+mode exists in cache.
        Returns cached answer dict or None.
        """
        with self._lock:
            if self._embeddings is None or len(self._entries) == 0:
                return None

            # Ensure embedding is 1D normalized
            qe = question_embedding.flatten().astype(np.float32)
            norm = np.linalg.norm(qe)
            if norm > 0:
                qe = qe / norm

            # Cosine similarity (embeddings are already normalized)
            similarities = self._embeddings @ qe

            # Find best match with same mode
            best_sim = -1.0
            best_idx = -1
            for i, entry in enumerate(self._entries):
                if entry["mode"] == mode and similarities[i] > best_sim:
                    best_sim = similarities[i]
                    best_idx = i

            if best_idx >= 0 and best_sim >= SIMILARITY_THRESHOLD:
                entry = self._entries[best_idx]
                logger.info(
                    "Cache HIT: sim=%.4f question='%s...' -> cached='%s...'",
                    best_sim,
                    "",  # Don't log full question
                    entry["question"][:40],
                )
                # Update LRU timestamp (fire-and-forget)
                try:
                    update_cache_last_used(entry["id"])
                except Exception:
                    pass
                return {
                    "question": entry["question"],
                    "answer_text": entry["answer_text"],
                    "audio_id": entry["audio_id"],
                    "passages_json": entry["passages_json"],
                }

            logger.debug("Cache MISS: best_sim=%.4f (threshold=%.2f)", best_sim, SIMILARITY_THRESHOLD)
            return None

    def store(
        self,
        question_embedding: np.ndarray,
        question: str,
        answer_text: str,
        audio_id: Optional[str],
        mode: str,
        passages_json: str,
    ) -> None:
        """Add a new entry to the cache. Evicts LRU if over MAX_CACHE_SIZE."""
        # Normalize embedding
        emb = question_embedding.flatten().astype(np.float32)
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm

        embedding_blob = emb.tobytes()

        with self._lock:
            # LRU eviction — remove oldest entry if at capacity
            if len(self._entries) >= MAX_CACHE_SIZE:
                oldest_idx = len(self._entries) - 1  # entries loaded in last_used DESC order
                oldest_entry = self._entries[oldest_idx]
                try:
                    delete_cache_entry(oldest_entry["id"])
                except Exception:
                    pass
                self._entries.pop(oldest_idx)
                if self._embeddings is not None:
                    self._embeddings = np.delete(self._embeddings, oldest_idx, axis=0)
                logger.debug("Evicted oldest cache entry")

            # Save to SQLite
            cache_id = save_cache_entry(
                question, answer_text, audio_id, mode, passages_json, embedding_blob
            )

            # Add to in-memory arrays
            new_entry = {
                "id": cache_id,
                "question": question,
                "answer_text": answer_text,
                "audio_id": audio_id,
                "mode": mode,
                "passages_json": passages_json,
            }

            if self._embeddings is None:
                self._embeddings = emb.reshape(1, -1)
            else:
                self._embeddings = np.vstack([self._embeddings, emb.reshape(1, -1)])
            self._entries.append(new_entry)

            logger.info("Cached answer for question: '%s...' (total: %d)", question[:40], len(self._entries))
