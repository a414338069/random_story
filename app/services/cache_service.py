"""缓存服务 — 内存 LRU + SQLite 双层缓存"""
from __future__ import annotations

import json
import time
from collections import OrderedDict
from typing import Optional

_MAX_LRU_SIZE = 100
_TTL_SECONDS = 1800  # 30 分钟

# 内存 LRU 缓存
_lru_cache: OrderedDict[str, tuple[str, float]] = OrderedDict()  # key → (response_json, timestamp)


def _make_key(template_id: str, realm: str, category: str = "") -> str:
    """构建缓存 key"""
    return f"{template_id}:{realm}:{category}"


def get_cached(template_id: str, realm: str, category: str = "", db=None) -> Optional[dict]:
    """查询缓存：内存 → SQLite → 未命中"""
    key = _make_key(template_id, realm, category)

    # 1. 检查内存缓存
    if key in _lru_cache:
        response_json, timestamp = _lru_cache[key]
        if time.time() - timestamp <= _TTL_SECONDS:
            _lru_cache.move_to_end(key)  # LRU 更新
            return json.loads(response_json)
        del _lru_cache[key]  # TTL 过期

    # 2. 检查 SQLite（如果提供了 db 连接）
    if db is not None:
        try:
            row = db.execute(
                "SELECT response, created_at FROM ai_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
            if row:
                response_text = row[0]
                created_at = row[1]
                if time.time() - float(created_at) <= _TTL_SECONDS:
                    # 回填内存缓存
                    _lru_cache[key] = (response_text, float(created_at))
                    _lru_cache.move_to_end(key)
                    return json.loads(response_text)
                db.execute("DELETE FROM ai_cache WHERE cache_key = ?", (key,))
                db.commit()
        except Exception:
            pass

    return None


def set_cached(template_id: str, realm: str, category: str, response: dict, db=None) -> None:
    """写入缓存：内存 + SQLite"""
    key = _make_key(template_id, realm, category)
    response_json = json.dumps(response, ensure_ascii=False)
    timestamp = time.time()

    # 1. 写入内存 LRU
    if key in _lru_cache:
        _lru_cache.move_to_end(key)
    _lru_cache[key] = (response_json, timestamp)

    # LRU 淘汰
    while len(_lru_cache) > _MAX_LRU_SIZE:
        _lru_cache.popitem(last=False)

    # 2. 写入 SQLite（如果提供了 db 连接）
    if db is not None:
        try:
            db.execute(
                "INSERT OR REPLACE INTO ai_cache (cache_key, response, created_at) VALUES (?, ?, ?)",
                (key, response_json, str(timestamp)),
            )
            db.commit()
        except Exception:
            pass


def clear_cache() -> None:
    """清空内存缓存（测试用）"""
    _lru_cache.clear()
