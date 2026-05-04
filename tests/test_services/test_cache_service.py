"""Tests for cache service — in-memory LRU + SQLite two-tier cache."""

import json
import sqlite3
import time
from unittest.mock import patch

import pytest

from app.services.cache_service import (
    _MAX_LRU_SIZE,
    _TTL_SECONDS,
    _make_key,
    clear_cache,
    get_cached,
    set_cached,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _memory_db() -> sqlite3.Connection:
    """Create an in-memory SQLite database with the ai_cache table."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute(
        """
        CREATE TABLE ai_cache (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key  TEXT NOT NULL UNIQUE,
            response   TEXT NOT NULL DEFAULT '{}',
            hit_count  INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCacheMiss:
    def test_miss_first_query(self):
        clear_cache()
        result = get_cached("tpl_1", "筑基", "修炼")
        assert result is None


class TestCacheHit:
    def test_hit_after_set(self):
        clear_cache()
        response = {"narrative": "test", "options": []}
        set_cached("tpl_1", "筑基", "修炼", response)
        result = get_cached("tpl_1", "筑基", "修炼")
        assert result == response


class TestTTL:
    def test_ttl_expired(self):
        clear_cache()
        frozen = 1000.0

        with patch("app.services.cache_service.time") as mock_time:
            mock_time.time.return_value = frozen
            response = {"narrative": "old", "options": []}
            set_cached("tpl_1", "筑基", "修炼", response)

            # Advance time past TTL
            mock_time.time.return_value = frozen + _TTL_SECONDS + 1
            result = get_cached("tpl_1", "筑基", "修炼")

        assert result is None


class TestLRUEviction:
    def test_lru_eviction(self):
        clear_cache()

        # Insert MAX_LRU_SIZE + 1 entries
        for i in range(_MAX_LRU_SIZE + 1):
            set_cached(f"tpl_{i}", "筑基", "修炼", {"narrative": str(i), "options": []})

        # Earliest entry (index 0) should be evicted
        assert get_cached("tpl_0", "筑基", "修炼") is None

        # Latest entry (index MAX) should still be present
        assert get_cached(f"tpl_{_MAX_LRU_SIZE}", "筑基", "修炼") == {
            "narrative": str(_MAX_LRU_SIZE),
            "options": [],
        }


class TestSQLiteFallback:
    def test_sqlite_fallback(self):
        """Memory miss → SQLite hit → backfill memory cache."""
        clear_cache()
        db = _memory_db()

        response = {"narrative": "sqlite cached", "options": [{"id": "a", "text": "A"}]}
        response_json = json.dumps(response, ensure_ascii=False)
        timestamp = str(time.time())

        db.execute(
            "INSERT INTO ai_cache (cache_key, response, created_at) VALUES (?, ?, ?)",
            ("tpl_1:筑基:修炼", response_json, timestamp),
        )
        db.commit()

        # Memory cache is empty → should read from SQLite
        result = get_cached("tpl_1", "筑基", "修炼", db=db)
        assert result == response

        # Verify backfill in memory cache
        from app.services.cache_service import _lru_cache

        assert "tpl_1:筑基:修炼" in _lru_cache


class TestKeyFormat:
    def test_key_format(self):
        assert _make_key("tpl_1", "筑基", "修炼") == "tpl_1:筑基:修炼"

    def test_key_format_without_category(self):
        assert _make_key("tpl_1", "筑基") == "tpl_1:筑基:"
