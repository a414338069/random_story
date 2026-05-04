"""AI service — DeepSeek API wrapper with JSON mode and retry logic."""
from __future__ import annotations

import json
import logging
import time

from openai import APIConnectionError, APIError, OpenAI

from app.config import Settings

logger = logging.getLogger(__name__)

_EMPTY_RESULT = {"narrative": "", "options": []}


class DeepSeekService:
    def __init__(self, settings: Settings | None = None):
        if settings is None:
            from app.dependencies import get_config
            settings = get_config()
        self._client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self._model = settings.DEEPSEEK_MODEL
        self._max_retries = 2

    def generate_event(self, prompt: str, context: dict) -> dict:
        messages = [
            {"role": "system", "content": "你是修仙世界的叙事生成器。你必须以JSON格式返回结果。"},
            {"role": "user", "content": prompt},
        ]

        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.8,
                    max_tokens=1000,
                )

                content = response.choices[0].message.content

                if not content or content.strip() == "":
                    if attempt < self._max_retries:
                        time.sleep(1)
                        continue
                    return _EMPTY_RESULT

                return json.loads(content)

            except (APIError, APIConnectionError) as e:
                last_error = e
                if attempt < self._max_retries:
                    wait = 2 ** attempt + 1
                    logger.warning(f"AI API error (attempt {attempt+1}): {e}, retrying in {wait}s")
                    time.sleep(wait)
            except json.JSONDecodeError as e:
                logger.error(f"AI returned invalid JSON: {e}")
                return _EMPTY_RESULT

        logger.error(f"AI service failed after {self._max_retries + 1} attempts: {last_error}")
        return _EMPTY_RESULT


class MockAIService:
    def __init__(self, response: dict | None = None):
        self._response = response or {
            "narrative": "你在山间修炼，灵气充裕，修为有所增长。",
            "options": [
                {"id": "opt1", "text": "继续修炼"},
                {"id": "opt2", "text": "下山历练"},
            ],
        }
        self.call_count = 0

    def generate_event(self, prompt: str, context: dict) -> dict:
        self.call_count += 1
        return self._response
