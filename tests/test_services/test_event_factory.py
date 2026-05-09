"""Tests for event_factory — 4-tier AI layered generation strategy with cascade."""

from unittest.mock import patch

import pytest

from app.services.event_factory import (
    generate_event,
    generate_l1_narrative,
    generate_l2_template,
    should_use_ai,
)


def _make_event_ctx(event_type: str, narrative_only: bool = False, **kwargs) -> dict:
    """Build a minimal event_ctx resembling the output of event_engine.build_event_context()."""
    ctx = {
        "event_type": event_type,
        "title": f"Test {event_type}",
        "prompt": "Test prompt for AI generation.",
        "fallback_narrative": f"Fallback narrative for {event_type}.",
        "default_options": [
            {"id": "opt1", "text": "Option A", "consequences": {"cultivation_gain": 5}},
            {"id": "opt2", "text": "Option B", "consequences": {"cultivation_gain": 3}},
        ],
        "narrative_only": narrative_only,
        "player": {"realm": "炼气"},
        "template": {
            "type": event_type,
            "narrative_only": narrative_only,
            "event_tier": kwargs.get("event_tier", "L3"),
        },
    }
    return ctx


def _make_state(event_count: int = 0, **kwargs) -> dict:
    return {
        "event_count": event_count,
        "realm": "炼气",
        "realm_progress": 0.5,
        "faction": "",
        "attributes": {"rootBone": 5, "comprehension": 3, "mindset": 1, "luck": 1},
        **kwargs,
    }


class TestShouldUseAi:
    """Tier decision logic for all event types."""

    def test_l1_narrative_only(self):
        ctx = _make_event_ctx("daily", narrative_only=True)
        assert should_use_ai(ctx) == "L1"

    def test_l1_childhood(self):
        assert should_use_ai(_make_event_ctx("childhood")) == "L1"

    def test_l1_birth(self):
        assert should_use_ai(_make_event_ctx("birth")) == "L1"

    def test_l1_youth(self):
        assert should_use_ai(_make_event_ctx("youth")) == "L1"

    def test_l1_explicit_tier(self):
        ctx = _make_event_ctx("daily", event_tier="L1")
        assert should_use_ai(ctx) == "L1"

    def test_l4_bottleneck(self):
        assert should_use_ai(_make_event_ctx("bottleneck")) == "L4"

    def test_l3_adventure(self):
        assert should_use_ai(_make_event_ctx("adventure")) == "L3"

    def test_l3_combat(self):
        assert should_use_ai(_make_event_ctx("combat")) == "L3"

    def test_l3_social(self):
        assert should_use_ai(_make_event_ctx("social")) == "L3"

    def test_l3_explore(self):
        assert should_use_ai(_make_event_ctx("explore")) == "L3"

    def test_l3_heavenly(self):
        assert should_use_ai(_make_event_ctx("heavenly")) == "L3"

    def test_l3_fortune(self):
        assert should_use_ai(_make_event_ctx("fortune")) == "L3"

    def test_l2_daily(self):
        assert should_use_ai(_make_event_ctx("daily")) == "L2"

    def test_l2_economy(self):
        assert should_use_ai(_make_event_ctx("economy")) == "L2"

    def test_l2_emotional(self):
        assert should_use_ai(_make_event_ctx("emotional")) == "L2"

    def test_l2_stones(self):
        assert should_use_ai(_make_event_ctx("stones")) == "L2"

    def test_l2_sect(self):
        assert should_use_ai(_make_event_ctx("sect")) == "L2"

    def test_soft_cap_30_events(self):
        ctx = _make_event_ctx("adventure")
        state = _make_state(event_count=30)
        assert should_use_ai(ctx, state) == "L2"

    def test_soft_cap_31_events(self):
        ctx = _make_event_ctx("adventure")
        state = _make_state(event_count=31)
        assert should_use_ai(ctx, state) == "L2"

    def test_soft_cap_does_not_affect_l1(self):
        ctx = _make_event_ctx("childhood")
        state = _make_state(event_count=50)
        assert should_use_ai(ctx, state) == "L1"

    def test_no_soft_cap_below_30(self):
        ctx = _make_event_ctx("adventure")
        state = _make_state(event_count=29)
        assert should_use_ai(ctx, state) == "L3"

    def test_event_tier_from_template(self):
        ctx = _make_event_ctx("unknown_type", event_tier="L1")
        assert should_use_ai(ctx) == "L1"

    def test_fallback_to_l3(self):
        ctx = _make_event_ctx("nonexistent", event_tier="L3")
        assert should_use_ai(ctx) == "L3"

    def test_without_state(self):
        assert should_use_ai(_make_event_ctx("adventure"), None) == "L3"

    def test_template_found_in_event_ctx(self):
        template = {"type": "bottleneck", "narrative_only": False, "event_tier": "L3"}
        ctx = {"template": template, "event_type": "bottleneck"}
        assert should_use_ai(ctx) == "L4"


class TestGenerateL1Narrative:

    def test_returns_narrative_and_options(self):
        ctx = _make_event_ctx("daily")
        result = generate_l1_narrative(ctx)
        assert "narrative" in result
        assert "options" in result
        assert result["_tier"] == "L1"
        assert isinstance(result["narrative"], str)
        assert len(result["narrative"]) > 0

    def test_narrative_only_returns_empty_options(self):
        ctx = _make_event_ctx("daily", narrative_only=True)
        result = generate_l1_narrative(ctx)
        assert result["options"] == []

    def test_childhood_uses_childhood_pool(self):
        """When no fallback_narrative, random childhood pool is used."""
        ctx = _make_event_ctx("childhood")
        ctx["fallback_narrative"] = ""  # clear fallback to force pool usage
        seen: set = set()
        for _ in range(30):
            result = generate_l1_narrative(ctx)
            seen.add(result["narrative"])
        assert len(seen) > 1

    def test_fallback_narrative_preferred_over_pool(self):
        """When fallback_narrative exists, it should be used instead of pool."""
        ctx = _make_event_ctx("childhood")
        ctx["fallback_narrative"] = "Custom baby smile narrative."
        result = generate_l1_narrative(ctx)
        assert result["narrative"] == "Custom baby smile narrative."

    def test_birth_returns_narrative(self):
        ctx = _make_event_ctx("birth")
        result = generate_l1_narrative(ctx)
        assert len(result["narrative"]) > 0

    def test_falls_back_to_yaml_fallback_when_no_pool(self):
        ctx = {
            "event_type": "unknown",
            "fallback_narrative": "Custom fallback text.",
            "default_options": [],
            "narrative_only": False,
        }
        result = generate_l1_narrative(ctx)
        assert len(result["narrative"]) > 0

    def test_uses_default_options_when_provided(self):
        custom_opts = [{"id": "custom1", "text": "Custom option"}]
        ctx = _make_event_ctx("daily")
        ctx["default_options"] = custom_opts
        result = generate_l1_narrative(ctx)
        assert result["options"] == custom_opts


class TestGenerateL2Template:

    def test_returns_formatted_narrative(self):
        ctx = _make_event_ctx("daily")
        state = _make_state()
        result = generate_l2_template(ctx, state)
        assert result["_tier"] == "L2"
        assert len(result["narrative"]) > 0
        assert len(result["options"]) >= 2

    def test_includes_location_placeholder_expanded(self):
        ctx = _make_event_ctx("daily")
        state = _make_state(faction="青云宗")
        result = generate_l2_template(ctx, state)
        assert "青云宗" in result["narrative"]

    def test_economy_has_items_placeholder(self):
        ctx = _make_event_ctx("economy")
        state = _make_state()
        result = generate_l2_template(ctx, state)
        assert len(result["narrative"]) > 0
        assert len(result["options"]) == 3

    def test_emotional_has_three_options(self):
        ctx = _make_event_ctx("emotional")
        result = generate_l2_template(ctx)
        assert len(result["options"]) == 3

    def test_stones_has_template(self):
        ctx = _make_event_ctx("stones")
        result = generate_l2_template(ctx)
        assert len(result["narrative"]) > 0

    def test_sect_has_template(self):
        ctx = _make_event_ctx("sect")
        result = generate_l2_template(ctx)
        assert len(result["narrative"]) > 0

    def test_unknown_type_falls_back_to_daily(self):
        ctx = _make_event_ctx("unknown")
        result = generate_l2_template(ctx)
        assert len(result["options"]) >= 2

    def test_falls_back_to_yaml_fallback(self):
        ctx = {
            "event_type": "daily",
            "fallback_narrative": "Template fallback narrative.",
            "default_options": [],
            "player": {"realm": "凡人"},
        }
        result = generate_l2_template(ctx)
        assert len(result["narrative"]) > 0

    def test_cultivation_desc_reflects_progress(self):
        import random
        random.seed(42)
        ctx = _make_event_ctx("daily")
        high_progress_state = _make_state(realm_progress=0.85)
        result = generate_l2_template(ctx, high_progress_state)
        from app.services.event_factory import _fmt_cultivation_desc
        desc = _fmt_cultivation_desc(ctx, high_progress_state)
        assert "突破" in desc
        assert len(result["narrative"]) > 0

    def test_location_reflects_faction(self):
        ctx = _make_event_ctx("daily")
        state = _make_state(faction="万剑宗")
        result = generate_l2_template(ctx, state)
        assert "万剑宗" in result["narrative"]


class TestGenerateEvent:

    def test_l1_events_go_to_l1(self):
        ctx = _make_event_ctx("childhood")
        result = generate_event(ctx)
        assert result["_tier"] == "L1"
        assert len(result["narrative"]) > 0

    def test_l2_events_go_to_l2(self):
        ctx = _make_event_ctx("daily")
        result = generate_event(ctx)
        assert result["_tier"] == "L2"

    def test_l3_events_call_ai_and_succeed(self):
        ctx = _make_event_ctx("adventure")
        ai_service = MockAIService(response={
            "narrative": "AI generated adventure narrative.",
            "options": [{"id": "opt1", "text": "Explore"}],
        })
        result = generate_event(ctx, state=_make_state(), ai_service=ai_service, prompt="Test prompt")
        assert result["_tier"] == "L3"
        assert "AI generated" in result["narrative"]

    def test_l4_events_call_ai_and_succeed(self):
        ctx = _make_event_ctx("bottleneck")
        ai_service = MockAIService(response={
            "narrative": "AI generated bottleneck narrative.",
            "options": [{"id": "opt1", "text": "Push through"}],
        })
        result = generate_event(ctx, state=_make_state(), ai_service=ai_service, prompt="Test prompt")
        assert result["_tier"] == "L4"

    @patch("app.services.event_factory._call_deepseek", side_effect=RuntimeError("No API key"))
    def test_l3_cascade_to_l1_on_ai_failure(self, _mock_ds):
        ctx = _make_event_ctx("adventure")
        ai_service = MockAIService(should_fail=True)
        result = generate_event(ctx, state=_make_state(), ai_service=ai_service, prompt="Test prompt")
        assert result["_tier"] == "L1"

    @patch("app.services.event_factory._call_deepseek", side_effect=RuntimeError("No API key"))
    def test_l4_cascade_to_l3_then_l1_on_double_failure(self, _mock_ds):
        ctx = _make_event_ctx("bottleneck")
        ai_service = MockAIService(should_fail=True)
        result = generate_event(ctx, state=_make_state(), ai_service=ai_service, prompt="Test prompt")
        assert result["_tier"] == "L1"

    def test_soft_cap_makes_l3_events_l2(self):
        ctx = _make_event_ctx("adventure")
        state = _make_state(event_count=35)
        result = generate_event(ctx, state=state)
        assert result["_tier"] == "L2"

    def test_result_always_has_narrative(self):
        ctx = _make_event_ctx("adventure")
        ai_service = MockAIService(should_fail=True)
        result = generate_event(ctx, state=_make_state(), ai_service=ai_service, prompt="Test")
        assert len(result["narrative"]) > 0
        assert "options" in result

    def test_cascade_logs_warnings(self, caplog):
        import logging
        caplog.set_level(logging.INFO)

        with patch("app.services.event_factory._call_deepseek", side_effect=RuntimeError("No API key")):
            ctx = _make_event_ctx("adventure")
            ai_service = MockAIService(should_fail=True)
            generate_event(ctx, state=_make_state(), ai_service=ai_service, prompt="Test")

        assert any("Falling back to L1" in r.message for r in caplog.records)


class MockAIService:
    """Simulates AI service for testing cascade fallback."""

    def __init__(self, response: dict | None = None, should_fail: bool = False):
        self._response = response or {
            "narrative": "Mock narrative.",
            "options": [{"id": "opt1", "text": "Mock option"}],
        }
        self._should_fail = should_fail
        self.call_count = 0

    def generate_event(self, prompt: str, context: dict, skip_ai: bool = False) -> dict:
        self.call_count += 1
        if self._should_fail:
            raise RuntimeError("Simulated AI failure")
        return self._response


class TestEdgeCases:

    def test_should_use_ai_with_no_template_key(self):
        ctx = {"event_type": "bottleneck"}
        assert should_use_ai(ctx) == "L4"

    def test_should_use_ai_defaults_to_daily(self):
        ctx = {}
        assert should_use_ai(ctx) == "L2"

    @patch("app.services.event_factory._call_deepseek", side_effect=RuntimeError("No API key"))
    def test_generate_event_no_prompt_no_ai(self, _mock_ds):
        ctx = _make_event_ctx("adventure")
        ai_service = MockAIService(should_fail=True)
        result = generate_event(ctx, state=_make_state(), ai_service=ai_service)
        assert result["_tier"] == "L1"

    def test_generate_event_empty_state(self):
        ctx = _make_event_ctx("daily")
        result = generate_event(ctx, state={})
        assert result["_tier"] == "L2"

    def test_generate_l1_with_missing_fallback(self):
        ctx = {"event_type": "daily", "default_options": [], "narrative_only": False}
        result = generate_l1_narrative(ctx)
        assert len(result["narrative"]) > 0


class TierTrackingMockAI:
    """Mock AI service that tracks which tier was called and returns empty result.

    Used to verify the L4→L3→L1 cascade path.
    """

    def __init__(self):
        self.tiers_called: list[str] = []

    def generate_event(self, prompt: str, context: dict, skip_ai: bool = False) -> dict:
        model_hint = ""
        if "deepseek-v4-pro" in prompt:
            model_hint = "L4"
        elif "deepseek-v4-flash" in prompt:
            model_hint = "L3"
        self.tiers_called.append(model_hint)
        return {"narrative": "", "options": []}


class TestAICascadeL4ToL3ToL1:
    """Verify cascade: L4 fails → L3 attempted → L3 fails → L1 fallback."""

    @patch("app.services.event_factory._call_deepseek", side_effect=RuntimeError("No API key"))
    def test_l4_cascade_to_l3_then_to_l1(self, _mock_ds):
        ctx = _make_event_ctx("bottleneck")
        mock_ai = TierTrackingMockAI()
        result = generate_event(
            ctx,
            state=_make_state(),
            ai_service=mock_ai,
            prompt="Model: deepseek-v4-pro\nTest prompt",
        )

        assert result["_tier"] == "L1"
        assert len(result["narrative"]) > 0
        assert "options" in result

    @patch("app.services.event_factory._call_deepseek", side_effect=RuntimeError("No API key"))
    def test_l3_cascade_to_l1_directly(self, _mock_ds):
        ctx = _make_event_ctx("adventure")
        mock_ai = TierTrackingMockAI()
        result = generate_event(
            ctx,
            state=_make_state(),
            ai_service=mock_ai,
            prompt="Model: deepseek-v4-flash\nTest prompt",
        )

        assert result["_tier"] == "L1"
        assert len(result["narrative"]) > 0

    @patch("app.services.event_factory._call_deepseek")
    def test_l4_cascade_via_direct_call(self, mock_call):
        mock_call.return_value = {"narrative": "", "options": []}

        ctx = _make_event_ctx("bottleneck")
        result = generate_event(
            ctx,
            state=_make_state(),
            ai_service=None,
            prompt="Test prompt",
        )

        assert result["_tier"] == "L1"
        assert len(result["narrative"]) > 0
        assert mock_call.call_count == 2

    @patch("app.services.event_factory._call_deepseek")
    def test_l3_cascade_via_direct_call(self, mock_call):
        mock_call.return_value = {"narrative": "", "options": []}

        ctx = _make_event_ctx("adventure")
        result = generate_event(
            ctx,
            state=_make_state(),
            ai_service=None,
            prompt="Test prompt",
        )

        assert result["_tier"] == "L1"
        assert len(result["narrative"]) > 0
        assert mock_call.call_count == 1
