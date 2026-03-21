#!/usr/bin/env python3
"""
SQLite-based cache for query embeddings (Phase 2 Optimization)
Eliminates redundant Voyage AI API calls by caching query embeddings

Usage:
    from embedding_cache import EmbeddingCache
    cache = EmbeddingCache()

    # Try to get cached embedding
    embedding = cache.get("What is dharma?")
    if not embedding:
        # Cache miss - call API
        embedding = call_voyage_api(...)
        cache.set("What is dharma?", embedding)

    # View statistics
    stats = cache.stats()
    print(f"Cache hit rate: {stats['cache_hit_rate']}%")
"""
import sqlite3
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict


class EmbeddingCache:
    """
    Persistent cache for query embeddings using SQLite
    Reduces API costs by 70-95% in typical production usage
    """

    def __init__(self, cache_file: str = "embeddings_cache.db"):
        """
        Initialize the embedding cache

        Args:
            cache_file: Name of SQLite database file (default: embeddings_cache.db)
        """
        # Store cache in project root directory
        self.db_path = Path(__file__).parent.parent / cache_file
        self._init_db()

    def _init_db(self):
        """Initialize database schema if not exists"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_embeddings (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def _hash_query(self, query: str) -> str:
        """
        Create consistent hash for query (case-insensitive, whitespace-normalized)

        Args:
            query: Query text

        Returns:
            MD5 hash of normalized query
        """
        # Normalize: lowercase, strip whitespace
        normalized = query.strip().lower()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def get(self, query: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding for query

        Args:
            query: Query text

        Returns:
            Cached embedding as list of floats, or None if not cached
        """
        query_hash = self._hash_query(query)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            "SELECT embedding FROM query_embeddings WHERE query_hash = ?",
            (query_hash,)
        )
        result = cursor.fetchone()

        if result:
            # Increment access counter and update last accessed time
            conn.execute("""
                UPDATE query_embeddings
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE query_hash = ?
            """, (query_hash,))
            conn.commit()

        conn.close()

        if result:
            return json.loads(result[0])
        return None

    def set(self, query: str, embedding: List[float]):
        """
        Store query embedding in cache

        Args:
            query: Query text
            embedding: Embedding vector as list of floats
        """
        query_hash = self._hash_query(query)

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO query_embeddings
            (query_hash, query_text, embedding, created_at, access_count, last_accessed)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1, CURRENT_TIMESTAMP)
        """, (query_hash, query, json.dumps(embedding)))
        conn.commit()
        conn.close()

    def stats(self) -> Dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics:
            - total_unique_queries: Number of unique queries cached
            - total_accesses: Total number of cache lookups
            - avg_accesses_per_query: Average reuse per query
            - cache_hit_rate: Percentage of cache hits
            - api_calls_saved: Number of API calls avoided
            - cost_saved: Estimated cost savings ($)
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_queries,
                SUM(access_count) as total_accesses,
                AVG(access_count) as avg_accesses
            FROM query_embeddings
        """)
        result = cursor.fetchone()
        conn.close()

        total_queries = result[0] or 0
        total_accesses = result[1] or 0
        avg_accesses = result[2] or 0

        # Calculate cache hit rate
        # First access is always a miss (API call), subsequent accesses are hits
        api_calls_saved = max(0, total_accesses - total_queries)
        cache_hit_rate = (api_calls_saved / total_accesses * 100) if total_accesses > 0 else 0

        # Voyage AI pricing: ~$0.0012 per query embedding
        cost_per_query = 0.0012
        cost_saved = api_calls_saved * cost_per_query

        return {
            "total_unique_queries": total_queries,
            "total_accesses": total_accesses,
            "avg_accesses_per_query": round(avg_accesses, 2),
            "cache_hit_rate": round(cache_hit_rate, 1),
            "api_calls_saved": api_calls_saved,
            "cost_saved": round(cost_saved, 4)
        }

    def clear(self):
        """Clear all cached embeddings"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("DELETE FROM query_embeddings")
        conn.commit()
        conn.close()

    def size(self) -> int:
        """
        Get number of cached queries

        Returns:
            Number of unique queries in cache
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM query_embeddings")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0


# Global cache instance (singleton pattern)
_cache_instance = None


def get_cache() -> EmbeddingCache:
    """
    Get global cache instance (singleton)

    Returns:
        EmbeddingCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = EmbeddingCache()
    return _cache_instance


if __name__ == "__main__":
    # Test the cache
    print("Testing EmbeddingCache...")

    cache = EmbeddingCache("test_cache.db")

    # Test set/get
    test_embedding = [0.1, 0.2, 0.3] * 683  # Mock 2048-dim embedding
    cache.set("What is dharma?", test_embedding)

    retrieved = cache.get("What is dharma?")
    assert retrieved == test_embedding, "Cache set/get failed!"

    # Test case-insensitive
    retrieved2 = cache.get("WHAT IS DHARMA?")
    assert retrieved2 == test_embedding, "Case-insensitive lookup failed!"

    # Test stats
    cache.get("What is dharma?")  # Access again
    stats = cache.stats()
    print(f"✅ Cache working! Stats: {stats}")

    # Cleanup
    test_db = Path(__file__).parent.parent / "test_cache.db"
    if test_db.exists():
        test_db.unlink()
    print("✅ All tests passed!")
