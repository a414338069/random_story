"""Tests for AI service — DeepSeek API wrapper, JSON mode, retry logic."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.dependencies import AIServiceProtocol


# ---------------------------------------------------------------------------
# MockAIService tests
# ---------------------------------------------------------------------------


class TestMockAIService:
    def test_mock_service_returns_valid_json(self):
        from app.services.ai_service import MockAIService

        svc = MockAIService()
        result = svc.generate_event("test prompt", {})
        assert isinstance(result, dict)
        assert "narrative" in result
        assert "options" in result

    def test_mock_service_tracks_calls(self):
        from app.services.ai_service import MockAIService

        svc = MockAIService()
        assert svc.call_count == 0
        svc.generate_event("a", {})
        assert svc.call_count == 1
        svc.generate_event("b", {})
        assert svc.call_count == 2

    def test_mock_service_custom_response(self):
        from app.services.ai_service import MockAIService

        custom = {"narrative": "custom", "options": [{"id": "x", "text": "X"}]}
        svc = MockAIService(response=custom)
        result = svc.generate_event("", {})
        assert result == custom


# ---------------------------------------------------------------------------
# DeepSeekService tests (all mocked — no real HTTP)
# ---------------------------------------------------------------------------


def _make_settings(api_key: str = "sk-test") -> object:
    """Create a Settings-like object for testing."""
    from app.config import Settings

    return Settings(DEEPSEEK_API_KEY=api_key)


def _mock_completion(content: str):
    """Build a mock OpenAI completion response."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    resp = MagicMock()
    resp.choices = [choice]
    return resp


class TestDeepSeekRetryOn500:
    """APIError triggers retry up to max_retries times."""

    @patch("app.services.ai_service.OpenAI")
    def test_retries_on_api_error(self, MockOpenAI):
        from openai import APIError

        from app.services.ai_service import DeepSeekService

        client = MockOpenAI.return_value
        client.chat.completions.create.side_effect = APIError(
            message="server error",
            request=MagicMock(),
            body=None,
        )

        svc = DeepSeekService(settings=_make_settings())
        result = svc.generate_event("test", {})

        # Should have retried max_retries + 1 total attempts
        assert client.chat.completions.create.call_count == svc._max_retries + 1
        # Fallback empty result
        assert result == {"narrative": "", "options": []}


class TestDeepSeekEmptyContentRetry:
    """Empty content string triggers retry."""

    @patch("app.services.ai_service.OpenAI")
    def test_empty_content_retries_once(self, MockOpenAI):
        from app.services.ai_service import DeepSeekService

        client = MockOpenAI.return_value
        # First call returns empty, second returns valid JSON
        client.chat.completions.create.side_effect = [
            _mock_completion(""),
            _mock_completion('{"narrative": "recovered", "options": []}'),
        ]

        svc = DeepSeekService(settings=_make_settings())
        result = svc.generate_event("test", {})

        assert result == {"narrative": "recovered", "options": []}
        assert client.chat.completions.create.call_count == 2


class TestDeepSeekJsonParse:
    """Normal JSON string response parsed correctly."""

    @patch("app.services.ai_service.OpenAI")
    def test_valid_json_parsed(self, MockOpenAI):
        from app.services.ai_service import DeepSeekService

        expected = {
            "narrative": "你在山间修炼，灵气充裕。",
            "options": [{"id": "opt1", "text": "继续修炼"}],
        }
        client = MockOpenAI.return_value
        client.chat.completions.create.return_value = _mock_completion(
            json.dumps(expected, ensure_ascii=False)
        )

        svc = DeepSeekService(settings=_make_settings())
        result = svc.generate_event("修炼", {})

        assert result == expected


class TestDeepSeekInvalidJsonFallback:
    """Invalid JSON string → fallback empty result."""

    @patch("app.services.ai_service.OpenAI")
    def test_invalid_json_fallback(self, MockOpenAI):
        from app.services.ai_service import DeepSeekService

        client = MockOpenAI.return_value
        client.chat.completions.create.return_value = _mock_completion(
            "this is not json"
        )

        svc = DeepSeekService(settings=_make_settings())
        result = svc.generate_event("test", {})

        assert result == {"narrative": "", "options": []}


class TestProtocolCompliance:
    def test_deepseek_satisfies_protocol(self):
        from app.services.ai_service import DeepSeekService

        svc = DeepSeekService.__new__(DeepSeekService)
        assert hasattr(svc, "generate_event")
        assert callable(svc.generate_event)

    def test_mock_satisfies_protocol(self):
        from app.services.ai_service import MockAIService

        svc = MockAIService()
        assert hasattr(svc, "generate_event")
        assert callable(svc.generate_event)
