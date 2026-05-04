"""Tests for configuration management — Settings + DI functions."""

import os
from pathlib import Path

import pytest

from app.config import Settings
from app.dependencies import AIServiceProtocol, get_ai_service, get_config, get_db


class TestSettingsDefaults:
    """Verify Settings loads correct default values when no env is set."""

    def test_default_values(self):
        """All fields should have expected defaults when no .env or env vars."""
        settings = Settings(_env_file=None)
        assert settings.DEEPSEEK_API_KEY == ""
        assert settings.DEEPSEEK_MODEL == "deepseek-v4-flash"
        assert settings.DEEPSEEK_BASE_URL == "https://api.deepseek.com"
        assert settings.DATABASE_PATH == "app/data/rebirth.db"
        assert settings.CORS_ORIGINS == "*"
        assert settings.MAX_EVENTS_PER_GAME == 60
        assert settings.CACHE_TTL == 1800

    def test_max_events_is_int(self):
        """MAX_EVENTS_PER_GAME must be typed as int."""
        settings = Settings(_env_file=None)
        assert isinstance(settings.MAX_EVENTS_PER_GAME, int)

    def test_cache_ttl_is_int(self):
        """CACHE_TTL must be typed as int."""
        settings = Settings(_env_file=None)
        assert isinstance(settings.CACHE_TTL, int)

    def test_database_path_default_location(self):
        """DATABASE_PATH must default to app/data/rebirth.db."""
        settings = Settings(_env_file=None)
        assert settings.DATABASE_PATH == "app/data/rebirth.db"


class TestSettingsEnvOverrides:
    """Verify env vars correctly override defaults."""

    def test_env_var_override(self, monkeypatch):
        """Setting DEEPSEEK_MODEL env var overrides the default."""
        monkeypatch.setenv("DEEPSEEK_MODEL", "test-model")
        settings = Settings(_env_file=None)
        assert settings.DEEPSEEK_MODEL == "test-model"

    def test_env_var_override_multiple(self, monkeypatch):
        """Multiple env vars override their respective defaults."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        monkeypatch.setenv("MAX_EVENTS_PER_GAME", "30")
        monkeypatch.setenv("CACHE_TTL", "900")
        settings = Settings(_env_file=None)
        assert settings.DEEPSEEK_API_KEY == "sk-test-key"
        assert settings.MAX_EVENTS_PER_GAME == 30
        assert settings.CACHE_TTL == 900

    def test_env_var_overrides_dotenv(self, monkeypatch, tmp_path):
        """Env vars take precedence over .env file values."""
        dotenv = tmp_path / ".env"
        dotenv.write_text("DEEPSEEK_MODEL=from-dotenv\n")
        monkeypatch.setenv("DEEPSEEK_MODEL", "from-env")
        settings = Settings(_env_file=str(dotenv))
        assert settings.DEEPSEEK_MODEL == "from-env"

    def test_missing_api_key_no_error(self):
        """Absence of DEEPSEEK_API_KEY must not cause an error."""
        if "DEEPSEEK_API_KEY" in os.environ:
            saved = os.environ.pop("DEEPSEEK_API_KEY")
            try:
                settings = Settings(_env_file=None)
                assert settings.DEEPSEEK_API_KEY == ""
            finally:
                os.environ["DEEPSEEK_API_KEY"] = saved
        else:
            settings = Settings(_env_file=None)
            assert settings.DEEPSEEK_API_KEY == ""


class TestSettingsDotEnvFile:
    """Verify .env file loading."""

    def test_dotenv_loading(self, tmp_path):
        """Settings should read values from a .env file."""
        dotenv = tmp_path / ".env"
        dotenv.write_text(
            "DEEPSEEK_API_KEY=sk-dotenv-key\n"
            "DEEPSEEK_MODEL=dotenv-model\n"
            "MAX_EVENTS_PER_GAME=42\n"
        )
        settings = Settings(_env_file=str(dotenv))
        assert settings.DEEPSEEK_API_KEY == "sk-dotenv-key"
        assert settings.DEEPSEEK_MODEL == "dotenv-model"
        assert settings.MAX_EVENTS_PER_GAME == 42

    def test_dotenv_partial_override(self, tmp_path):
        """Only specified .env fields override defaults; others stay."""
        dotenv = tmp_path / ".env"
        dotenv.write_text("DEEPSEEK_API_KEY=sk-partial\n")
        settings = Settings(_env_file=str(dotenv))
        assert settings.DEEPSEEK_API_KEY == "sk-partial"
        assert settings.DEEPSEEK_MODEL == "deepseek-v4-flash"
        assert settings.CORS_ORIGINS == "*"


class TestGetConfig:
    """Verify get_config() returns Settings."""

    def test_get_config_returns_settings(self):
        """get_config() should return a Settings instance."""
        config = get_config()
        assert isinstance(config, Settings)

    def test_get_config_lazy(self):
        """get_config() should be callable multiple times (singleton)."""
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2


class TestGetDB:
    """Verify get_db() in dependencies delegates to database module."""

    def test_get_db_returns_connection(self):
        """get_db() should return a working sqlite3 connection."""
        conn = get_db(":memory:")
        assert conn is not None
        row = conn.execute("SELECT 1 AS x").fetchone()
        assert row["x"] == 1
        conn.close()

    def test_get_db_default_creates_dir(self, monkeypatch, tmp_path):
        """get_db() with default path should create parent directory."""
        import app.database as db_mod
        monkeypatch.setattr(db_mod, "DEFAULT_DB_PATH", str(tmp_path / "sub" / "test.db"))
        monkeypatch.setattr(db_mod, "_DEFAULT_DB_DIR", str(tmp_path / "sub"))
        conn = get_db()
        assert (tmp_path / "sub" / "test.db").exists()
        conn.close()

    def test_get_db_memory(self):
        """get_db(':memory:') returns an in-memory database."""
        conn = get_db(":memory:")
        assert conn is not None
        conn.close()


class TestGetAIService:
    """Verify get_ai_service() returns an AIServiceProtocol."""

    def test_get_ai_service_returns_protocol_instance(self):
        """get_ai_service() should return an object conforming to AIServiceProtocol."""
        service = get_ai_service()
        assert hasattr(service, "generate_event")
        assert callable(service.generate_event)

    def test_generate_event_method_signature(self):
        """generate_event should accept (prompt, context) and return dict."""
        service = get_ai_service()
        import inspect
        sig = inspect.signature(service.generate_event)
        params = list(sig.parameters.keys())
        assert "prompt" in params
        assert "context" in params

    def test_aiserviceprotocol_is_protocol(self):
        """AIServiceProtocol should be a typing.Protocol."""
        from typing import Protocol as TypingProtocol
        assert issubclass(AIServiceProtocol, TypingProtocol)

    def test_aiserviceprotocol_method_signature(self):
        """AIServiceProtocol.generate_event should have (self, prompt, context) -> dict."""
        import inspect
        sig = inspect.signature(AIServiceProtocol.generate_event)
        assert "prompt" in sig.parameters
        assert "context" in sig.parameters
        assert sig.return_annotation == dict or str(sig.return_annotation) == "dict"
