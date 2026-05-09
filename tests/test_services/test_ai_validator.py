"""Tests for AI output validator — 3-layer validation + fallback template."""

import pytest

from app.services.ai_validator import (
    check_content_safety,
    check_narrative_option_alignment,
    parse_json_response,
    validate_ai_output,
    validate_schema,
)

# 20 字的有效叙事，用于 schema 校验测试
VALID_NARRATIVE = "你在山间修炼，灵气充裕，修为有所增长了。"


# ---------------------------------------------------------------------------
# Layer 1: JSON Parsing
# ---------------------------------------------------------------------------


class TestParseJsonResponse:
    def test_parse_valid_json(self):
        raw = '{"narrative": "你在山间修炼，灵气充裕。", "options": [{"id": "a", "text": "继续"}]}'
        result = parse_json_response(raw)
        assert result is not None
        assert result["narrative"] == "你在山间修炼，灵气充裕。"
        assert len(result["options"]) == 1

    def test_parse_markdown_json(self):
        raw = '```json\n{"narrative": "修炼中有所感悟。", "options": [{"id": "a", "text": "打坐"}]}\n```'
        result = parse_json_response(raw)
        assert result is not None
        assert result["narrative"] == "修炼中有所感悟。"

    def test_parse_invalid_returns_none(self):
        assert parse_json_response("this is not json") is None
        assert parse_json_response("") is None
        assert parse_json_response("```json\nnot json\n```") is None

    def test_parse_trims_whitespace(self):
        raw = '  \n  {"narrative": "测试叙事内容", "options": []}  \n  '
        result = parse_json_response(raw)
        assert result is not None
        assert result["narrative"] == "测试叙事内容"


# ---------------------------------------------------------------------------
# Layer 2: JSON Schema Validation
# ---------------------------------------------------------------------------


class TestValidateSchema:
    def test_schema_valid(self):
        data = {
            "narrative": VALID_NARRATIVE,
            "options": [
                {"id": "opt1", "text": "继续修炼"},
                {"id": "opt2", "text": "下山历练"},
            ],
        }
        is_valid, cleaned = validate_schema(data)
        assert is_valid is True
        assert "narrative" in cleaned
        assert len(cleaned["options"]) == 2

    def test_schema_narrative_too_short(self):
        data = {
            "narrative": "太短了",
            "options": [
                {"id": "opt1", "text": "继续"},
                {"id": "opt2", "text": "停止"},
            ],
        }
        is_valid, _ = validate_schema(data)
        assert is_valid is False

    def test_schema_narrative_too_long(self):
        data = {
            "narrative": "很" * 501,
            "options": [
                {"id": "opt1", "text": "继续"},
                {"id": "opt2", "text": "停止"},
            ],
        }
        is_valid, _ = validate_schema(data)
        assert is_valid is False

    def test_schema_options_too_few(self):
        data = {
            "narrative": VALID_NARRATIVE,
            "options": [{"id": "opt1", "text": "继续修炼"}],
        }
        is_valid, _ = validate_schema(data)
        assert is_valid is False

    def test_schema_options_too_many(self):
        data = {
            "narrative": VALID_NARRATIVE,
            "options": [
                {"id": "opt1", "text": "继续修炼"},
                {"id": "opt2", "text": "下山历练"},
                {"id": "opt3", "text": "闭关"},
                {"id": "opt4", "text": "飞升"},
            ],
        }
        is_valid, _ = validate_schema(data)
        assert is_valid is False

    def test_schema_removes_numeric_fields(self):
        data = {
            "narrative": VALID_NARRATIVE,
            "options": [
                {"id": "opt1", "text": "继续修炼", "cultivation_gain": 10},
                {"id": "opt2", "text": "下山历练"},
            ],
            "cultivation_gain": 5,
            "spirit_stones_gain": 100,
            "some_other_numeric": 42,
        }
        is_valid, cleaned = validate_schema(data)
        assert is_valid is True
        assert "cultivation_gain" not in cleaned
        assert "spirit_stones_gain" not in cleaned
        assert "some_other_numeric" not in cleaned
        assert "cultivation_gain" not in cleaned["options"][0]

    def test_schema_missing_narrative(self):
        data = {
            "options": [
                {"id": "opt1", "text": "继续"},
                {"id": "opt2", "text": "停止"},
            ],
        }
        is_valid, _ = validate_schema(data)
        assert is_valid is False

    def test_schema_missing_options(self):
        data = {"narrative": VALID_NARRATIVE}
        is_valid, _ = validate_schema(data)
        assert is_valid is False

    def test_schema_option_missing_id(self):
        data = {
            "narrative": VALID_NARRATIVE,
            "options": [
                {"text": "继续修炼"},
                {"id": "opt2", "text": "下山历练"},
            ],
        }
        is_valid, _ = validate_schema(data)
        assert is_valid is False

    def test_schema_option_missing_text(self):
        data = {
            "narrative": VALID_NARRATIVE,
            "options": [
                {"id": "opt1"},
                {"id": "opt2", "text": "下山历练"},
            ],
        }
        is_valid, _ = validate_schema(data)
        assert is_valid is False


# ---------------------------------------------------------------------------
# Layer 3: Content Safety
# ---------------------------------------------------------------------------


class TestCheckContentSafety:
    def test_safety_detect_forbidden(self):
        data = {
            "narrative": "你获得了一把枪，威力巨大。",
            "options": [
                {"id": "opt1", "text": "用手机联系道友"},
                {"id": "opt2", "text": "继续修炼"},
            ],
        }
        is_safe, cleaned = check_content_safety(data)
        assert is_safe is False
        assert "枪" not in cleaned["narrative"]
        assert "***" in cleaned["narrative"]
        assert "手机" not in cleaned["options"][0]["text"]
        assert "***" in cleaned["options"][0]["text"]

    def test_safety_clean_passes(self):
        data = {
            "narrative": "你在山间修炼，灵气充裕。",
            "options": [
                {"id": "opt1", "text": "继续修炼"},
                {"id": "opt2", "text": "下山历练"},
            ],
        }
        is_safe, cleaned = check_content_safety(data)
        assert is_safe is True
        assert cleaned == data


# ---------------------------------------------------------------------------
# Full Pipeline: validate_ai_output
# ---------------------------------------------------------------------------


class TestValidateAiOutput:
    DEFAULT_OPTIONS = [
        {"id": "default1", "text": "继续修炼"},
        {"id": "default2", "text": "原地休息"},
    ]

    def test_validate_full_pipeline(self):
        import json

        payload = json.dumps(
            {
                "narrative": VALID_NARRATIVE,
                "options": [
                    {"id": "opt1", "text": "继续修炼"},
                    {"id": "opt2", "text": "下山历练"},
                ],
            },
            ensure_ascii=False,
        )
        result = validate_ai_output(payload, "兜底叙事", self.DEFAULT_OPTIONS)
        assert result["narrative"] == VALID_NARRATIVE
        assert len(result["options"]) == 2

    def test_validate_fallback_on_invalid(self):
        result = validate_ai_output("not json", "兜底叙事内容", self.DEFAULT_OPTIONS)
        assert result["narrative"] == "兜底叙事内容"
        assert result["options"] == self.DEFAULT_OPTIONS

    def test_validate_fallback_on_schema_fail(self):
        raw = '{"narrative": "太短", "options": [{"id": "a", "text": "继续"}]}'
        result = validate_ai_output(raw, "兜底叙事内容", self.DEFAULT_OPTIONS)
        assert result["narrative"] == "兜底叙事内容"
        assert result["options"] == self.DEFAULT_OPTIONS

    def test_validate_fallback_options_pad(self):
        import json

        payload = json.dumps(
            {
                "narrative": VALID_NARRATIVE,
                "options": [
                    {"id": "opt1", "text": "继续修炼"},
                    {"id": "opt2", "text": "下山历练"},
                ],
            },
            ensure_ascii=False,
        )
        result = validate_ai_output(payload, "兜底叙事", self.DEFAULT_OPTIONS)
        assert len(result["options"]) >= 2

    def test_validate_cleans_forbidden_words(self):
        import json

        payload = json.dumps(
            {
                "narrative": "你获得了一把枪，威力巨大，令人震撼。",
                "options": [
                    {"id": "opt1", "text": "用微信联系道友"},
                    {"id": "opt2", "text": "继续修炼"},
                ],
            },
            ensure_ascii=False,
        )
        result = validate_ai_output(payload, "兜底叙事", self.DEFAULT_OPTIONS)
        assert "枪" not in result["narrative"]
        assert "微信" not in result["options"][0]["text"]


# ---------------------------------------------------------------------------
# Narrative-Option Alignment: check_narrative_option_alignment
# ---------------------------------------------------------------------------


def test_alignment_match_basic():
    """Options that reference narrative keywords should pass."""
    assert check_narrative_option_alignment(
        "老者看中你的灵草", [{"text": "你的灵草很珍贵"}]
    ) is True


def test_alignment_mismatch_basic():
    """Options unrelated to narrative should fail."""
    assert check_narrative_option_alignment(
        "老者看中你的灵草", [{"text": "购买丹药"}]
    ) is False


def test_alignment_empty_input():
    """Empty narrative or options should return True (pass through)."""
    assert check_narrative_option_alignment("", [{"text": "test"}]) is True
    assert check_narrative_option_alignment("narrative", []) is True


def test_alignment_all_match():
    """All options matching 3+ char keywords from narrative should pass."""
    assert check_narrative_option_alignment(
        "你在后山修炼功法",
        [{"text": "在后山修炼"}, {"text": "修炼功法入门"}],
    ) is True


def test_alignment_one_option_mismatch():
    """Any single option not matching 3+ char keyword should cause failure."""
    assert check_narrative_option_alignment(
        "你在后山修炼功法",
        [{"text": "在后山修炼"}, {"text": "去集市购物"}],
    ) is False


def test_alignment_no_chinese():
    """Non-Chinese text should pass through (no keywords extracted)."""
    assert check_narrative_option_alignment(
        "hello world", [{"text": "test"}]
    ) is True


def test_alignment_longer_narrative():
    """Longer narrative with richer 3+ char keyword set — all options match."""
    narrative = "白发老者手持断剑坐在山道旁休息"
    options = [
        {"text": "上前询问白发老者"},
        {"text": "手持断剑查看"},
        {"text": "坐在山道旁修炼"},
    ]
    assert check_narrative_option_alignment(narrative, options) is True
