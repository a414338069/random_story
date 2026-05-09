"""Tests for narrative-option alignment: should_use_ai tier fixing and keyword matching."""

import pytest

from app.services.event_factory import should_use_ai
from app.services.ai_validator import check_narrative_option_alignment


def _make_event_ctx(event_type: str, **kwargs) -> dict:
    """Build a minimal event_ctx with an embedded template dict for should_use_ai."""
    tpl = {
        "type": event_type,
        "event_tier": kwargs.get("event_tier", "L3"),
    }
    prompt_template = kwargs.get("prompt_template")
    if prompt_template is not None:
        tpl["prompt_template"] = prompt_template
    return {
        "event_type": event_type,
        "template": tpl,
        "player": {"realm": "炼气"},
    }


# ---------------------------------------------------------------------------
# should_use_ai — tier selection with explicit event_tier
# ---------------------------------------------------------------------------

class TestShouldUseAiHonorsEventTier:
    def test_honors_l3_tier_with_prompt_template(self):
        """Template with type=daily + event_tier=L3 + prompt_template → returns L3."""
        ctx = _make_event_ctx(
            "daily",
            event_tier="L3",
            prompt_template="宗门考核开始了，你需要选择一关主攻。",
        )
        assert should_use_ai(ctx) == "L3"

    def test_honors_l4_tier_with_prompt_template(self):
        """Template with type=daily + event_tier=L4 + prompt_template → returns L4."""
        ctx = _make_event_ctx(
            "daily",
            event_tier="L4",
            prompt_template="天劫降临，你必须在雷霆中找到一线生机。",
        )
        assert should_use_ai(ctx) == "L4"

    def test_falls_back_to_l2_without_prompt_template(self):
        """Template with type=daily + event_tier=L3 but NO prompt_template → returns L2."""
        ctx = _make_event_ctx("daily", event_tier="L3")
        # prompt_template is absent from the template dict
        assert should_use_ai(ctx) == "L2"

    def test_falls_back_to_l2_when_prompt_is_empty(self):
        """Template with type=daily + event_tier=L3 but empty prompt_template → returns L2."""
        ctx = _make_event_ctx("daily", event_tier="L3", prompt_template="")
        assert should_use_ai(ctx) == "L2"

    def test_type_sect_with_prompt_goes_to_l3(self):
        """Template with type=sect + event_tier=L3 + prompt_template → returns L3."""
        ctx = _make_event_ctx(
            "sect",
            event_tier="L3",
            prompt_template="金刚寺的试炼场上，师兄们正在以肉身硬抗灵兽攻击。",
        )
        assert should_use_ai(ctx) == "L3"

    def test_type_adventure_unchanged(self):
        """Type=adventure still returns L3 (existing behavior preserved)."""
        ctx = _make_event_ctx("adventure", event_tier="L3")
        assert should_use_ai(ctx) == "L3"

    def test_childhood_still_l1(self):
        """Childhood events remain L1 even with event_tier=L3."""
        ctx = _make_event_ctx(
            "childhood",
            event_tier="L3",
            prompt_template="你在村中奔跑嬉戏。",
        )
        assert should_use_ai(ctx) == "L1"


# ---------------------------------------------------------------------------
# check_narrative_option_alignment — keyword matching with 3+ char words
# ---------------------------------------------------------------------------

class TestCheckNarrativeOptionAlignment:
    def test_detects_mismatch_unrelated_topics(self):
        """Narrative about 万剑山庄, option about 星际飞船 → no 3+ char overlap → False."""
        narrative = "你站在万剑山庄的剑阁之中，三百六十五柄古剑悬于空中，剑气纵横如虹。"
        options = [
            {"id": "opt1", "text": "驾驶星际飞船逃离地球"},
            {"id": "opt2", "text": "使用激光炮消灭敌人"},
        ]
        assert check_narrative_option_alignment(narrative, options) is False

    def test_passes_when_keyword_matches(self):
        """Both options share 3+ char keywords with narrative → True."""
        narrative = "金刚寺的早课开始了，你与众僧一起诵经礼佛。"
        options = [
            {"id": "opt1", "text": "在金刚寺诵经"},
            {"id": "opt2", "text": "与众僧一同礼佛"},
        ]
        assert check_narrative_option_alignment(narrative, options) is True

    def test_passes_with_partial_overlap(self):
        """At least one 3+ char keyword in common per option → True."""
        narrative = "金刚寺的铜人阵中，武僧们施展轻功身法穿梭其中。"
        options = [
            {"id": "opt1", "text": "用金刚掌硬撼铜人阵"},
            {"id": "opt2", "text": "以轻功身法周旋"},
        ]
        assert check_narrative_option_alignment(narrative, options) is True

    def test_fails_when_one_option_has_no_overlap(self):
        """Even if some options match, ALL must have at least one 3+ char keyword."""
        narrative = "金刚寺的铜人阵中，武僧挥拳如风，你的金刚不坏之体尚未大成。"
        options = [
            {"id": "opt1", "text": "用金刚掌硬撼"},
            {"id": "opt2", "text": "吃掉苹果"},
        ]
        assert check_narrative_option_alignment(narrative, options) is False

    def test_empty_narrative_or_options_returns_true(self):
        """Boundary: empty narrative or no options → always True (no validation possible)."""
        assert check_narrative_option_alignment("", [{"id": "opt1", "text": "anything"}]) is True
        assert check_narrative_option_alignment("some narrative", []) is True

    def test_two_char_combinations_no_longer_match(self):
        """2-char substrings are excluded: '的剑' against option '用剑' → no 3+ char match → False."""
        narrative = "你握住手中的剑柄，剑光仿佛在呼吸。"
        options = [
            {"id": "opt1", "text": "用剑"},
        ]
        # "用剑" is 2 chars, and no 3+ char kernel from narrative appears in "用剑"
        assert check_narrative_option_alignment(narrative, options) is False

    def test_three_char_keyword_matches(self):
        """3-char substring '金刚寺' from narrative matches '金刚寺' in option → True."""
        narrative = "你第一次踏入金刚寺的大门，晨钟悠悠。"
        options = [
            {"id": "opt1", "text": "在金刚寺中参拜"},
        ]
        assert check_narrative_option_alignment(narrative, options) is True
