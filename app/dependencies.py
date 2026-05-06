import sqlite3
from functools import lru_cache
from typing import Protocol

from app.config import Settings


class AIServiceProtocol(Protocol):
    """Interface for AI narrative generation services."""

    def generate_event(self, prompt: str, context: dict, skip_ai: bool = False) -> dict: ...


@lru_cache
def get_config() -> Settings:
    return Settings()


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    from app.database import get_db as _get_db

    return _get_db(db_path)


def get_ai_service() -> AIServiceProtocol:
    """Return a stub AI service — real implementation will replace this."""

    class _StubAIService:
        def generate_event(self, prompt: str, context: dict, skip_ai: bool = False) -> dict:
            return {"event": prompt[:20], "options": []}

    return _StubAIService()
