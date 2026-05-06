"""Tests for event engine (Task 8)."""

import random

import pytest

from app.services.event_engine import (
    FALLBACK_EVENT,
    build_event_context,
    calculate_weights,
    filter_templates,
    load_templates,
    select_event,
    should_force_non_daily,
)


# ---------------------------------------------------------------------------
# load_templates()
# ---------------------------------------------------------------------------


def test_load_templates_has_test_events():
    """加载实际 YAML 事件模板并验证关键模板存在."""
    templates = load_templates()
    ids = {t["id"] for t in templates}
    assert "daily_010" in ids   # 通用 daily: 凡人-渡劫飞升
    assert "daily_004" in ids   # 金丹限定 daily


def test_load_templates_all_have_required_fields():
    """所有模板必须包含 8 个必要字段."""
    templates = load_templates()
    required = {
        "id", "type", "title", "trigger_conditions", "weight",
        "prompt_template", "fallback_narrative", "default_options",
    }
    for t in templates:
        assert required.issubset(t.keys()), f"Template {t.get('id', '?')} missing fields"


def test_load_templates_cached():
    """模块级缓存：两次调用返回同一个对象."""
    first = load_templates()
    second = load_templates()
    assert first is second


# ---------------------------------------------------------------------------
# filter_templates()
# ---------------------------------------------------------------------------


def test_filter_realm_min():
    """金丹限定事件不出现在凡人筛选中."""
    templates = load_templates()
    player = {"realm": "凡人", "age": 50, "faction": ""}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert "daily_010" in ids       # 凡人可访问
    assert "daily_004" not in ids   # 金丹限定


def test_filter_realm_exact_match():
    """金丹限定事件出现在金丹玩家筛选结果中."""
    templates = load_templates()
    player = {"realm": "金丹", "age": 300, "faction": ""}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert "daily_004" in ids   # 金丹限定, age 150-500
    assert "daily_010" in ids   # 全境界


def test_filter_realm_max_realm():
    """元婴境界超出金丹 max_realm 上限，不应匹配."""
    templates = load_templates()
    player = {"realm": "元婴", "age": 500, "faction": ""}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert "daily_004" not in ids   # max_realm=金丹


def test_filter_age_below_min():
    """年龄低于 min_age 不匹配."""
    templates = load_templates()
    player = {"realm": "金丹", "age": 50, "faction": ""}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert "daily_004" not in ids   # min_age=150


def test_filter_age_above_max():
    """年龄高于 max_age 不匹配."""
    templates = load_templates()
    player = {"realm": "金丹", "age": 2000, "faction": ""}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert "daily_004" not in ids   # max_age=500


def test_filter_age_in_range():
    """年龄在范围内匹配."""
    templates = load_templates()
    player = {"realm": "金丹", "age": 300, "faction": ""}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert "daily_004" in ids   # min_age=150, max_age=500


def test_filter_faction_null_allows_any():
    """required_faction=null 不限制门派."""
    templates = load_templates()
    player = {"realm": "金丹", "age": 300, "faction": "散修"}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert "daily_004" in ids   # no faction requirement


# ---------------------------------------------------------------------------
# calculate_weights()
# ---------------------------------------------------------------------------


def test_weights_daily():
    """日常类事件权重 = 1.0."""
    templates = load_templates()
    daily = [t for t in templates if t["type"] == "daily"]
    assert len(daily) >= 1
    player = {"realm": "凡人", "luck": 5, "cultivation": 0, "age": 50, "faction": ""}
    weighted = calculate_weights(daily, player)
    assert weighted[0][1] == 1.0


def test_weights_adventure_low_luck():
    """奇遇权重=0.3+luck×0.05, luck=0 → 0.3."""
    templates = load_templates()
    adv = [t for t in templates if t["type"] == "adventure"]
    assert len(adv) >= 1
    player = {"realm": "金丹", "luck": 0, "cultivation": 0, "age": 500, "faction": ""}
    weighted = calculate_weights(adv, player)
    assert weighted[0][1] == pytest.approx(0.3)


def test_weights_adventure_high_luck():
    """奇遇权重=0.3+luck×0.05, luck=10 → 0.8."""
    templates = load_templates()
    adv = [t for t in templates if t["type"] == "adventure"]
    player = {"realm": "金丹", "luck": 10, "cultivation": 0, "age": 500, "faction": ""}
    weighted = calculate_weights(adv, player)
    assert weighted[0][1] == pytest.approx(0.8)


def test_weights_bottleneck_partial():
    """筑基 cultivation_req=300, cultivation=150 → 0.5 + 150/300*0.5 = 0.75."""
    bottleneck_template = {
        "id": "test_bn",
        "type": "bottleneck",
        "title": "瓶颈突破",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999,
            "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "",
        "fallback_narrative": "",
        "default_options": [],
    }
    player = {"realm": "筑基", "luck": 5, "cultivation": 150, "age": 100, "faction": ""}
    weighted = calculate_weights([bottleneck_template], player)
    assert weighted[0][1] == pytest.approx(0.75)


def test_weights_bottleneck_zero_req():
    """凡人 cultivation_req=0 → 权重=1.0."""
    bottleneck_template = {
        "id": "test_bn_mortal",
        "type": "bottleneck",
        "title": "瓶颈突破",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999,
            "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "",
        "fallback_narrative": "",
        "default_options": [],
    }
    player = {"realm": "凡人", "luck": 5, "cultivation": 0, "age": 16, "faction": ""}
    weighted = calculate_weights([bottleneck_template], player)
    assert weighted[0][1] == pytest.approx(1.0)


def test_weights_bottleneck_none_req():
    """渡劫飞升 cultivation_req=None → 权重=1.0."""
    bottleneck_template = {
        "id": "test_bn_dujie",
        "type": "bottleneck",
        "title": "瓶颈突破",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999,
            "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "",
        "fallback_narrative": "",
        "default_options": [],
    }
    player = {"realm": "渡劫飞升", "luck": 5, "cultivation": 999999, "age": 1000, "faction": ""}
    weighted = calculate_weights([bottleneck_template], player)
    assert weighted[0][1] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# select_event()
# ---------------------------------------------------------------------------


def test_select_event_deterministic():
    """固定 seed 返回相同结果."""
    templates = load_templates()
    daily = [t for t in templates if t["type"] == "daily"]
    adv = [t for t in templates if t["type"] == "adventure"]
    all_t = daily + adv
    player = {"realm": "金丹", "luck": 5, "cultivation": 0, "age": 500, "faction": ""}
    weighted = calculate_weights(all_t, player)

    random.seed(42)
    e1 = select_event(weighted)
    random.seed(42)
    e2 = select_event(weighted)
    assert e1["id"] == e2["id"]


def test_select_event_returns_valid_template():
    """加权随机选择返回有效模板."""
    templates = load_templates()
    player = {"realm": "金丹", "luck": 5, "cultivation": 0, "age": 500, "faction": ""}
    filtered = filter_templates(templates, player)
    weighted = calculate_weights(filtered, player)

    random.seed(123)
    event = select_event(weighted)
    assert "id" in event
    assert "type" in event
    assert "title" in event


# ---------------------------------------------------------------------------
# select_event() — 空池返回兜底
# ---------------------------------------------------------------------------


def test_select_empty_returns_fallback():
    """空模板池返回硬编码 FALLBACK_EVENT."""
    event = select_event([])
    assert event is FALLBACK_EVENT
    assert "id" in event


# ---------------------------------------------------------------------------
# build_event_context()
# ---------------------------------------------------------------------------


def test_build_event_context():
    """构建 AI 上下文包含所有必要字段."""
    template = load_templates()[0]
    player = {"realm": "金丹", "age": 500, "faction": "万剑山庄", "luck": 5, "cultivation": 1200}
    ctx = build_event_context(template, player)
    assert "title" in ctx
    assert "prompt" in ctx
    assert "fallback_narrative" in ctx
    assert "default_options" in ctx
    assert "player" in ctx


def test_build_event_context_prompt_substitution():
    """prompt_template 中的 {age} 占位符应被替换."""
    templates = load_templates()
    template = next(t for t in templates if t["id"] == "daily_004")
    # daily_004 prompt: "你已{age}岁，金丹在丹田中缓缓旋转..."
    player = {"realm": "金丹", "age": 500, "faction": ""}
    ctx = build_event_context(template, player)
    assert "500" in ctx["prompt"]
    assert "{" not in ctx["prompt"]


# ---------------------------------------------------------------------------
# should_force_non_daily()
# ---------------------------------------------------------------------------


def test_force_non_daily_below_threshold():
    """连续日常次数 < 3 时不强制."""
    assert should_force_non_daily(0) is False
    assert should_force_non_daily(1) is False
    assert should_force_non_daily(2) is False


def test_force_non_daily_at_threshold():
    """连续日常次数 >= 3 时强制非日常."""
    assert should_force_non_daily(3) is True
    assert should_force_non_daily(5) is True


def test_force_non_daily_custom_threshold():
    """支持自定义阈值."""
    assert should_force_non_daily(3, threshold=5) is False
    assert should_force_non_daily(4, threshold=5) is False
    assert should_force_non_daily(5, threshold=5) is True


# ---------------------------------------------------------------------------
# filter_templates() — life-stage filtering (T2)
# ---------------------------------------------------------------------------


def _make_templates(*types_narrative: tuple[str, bool]) -> list[dict]:
    """Build synthetic templates with (type, narrative_only) pairs."""
    return [
        {
            "id": f"t{i}",
            "type": t,
            "title": f"template {i}",
            "trigger_conditions": {
                "min_realm": "凡人",
                "max_realm": "渡劫飞升",
                "min_age": 0,
                "max_age": 9999,
                "required_faction": None,
            },
            "weight": 1.0,
            "prompt_template": "",
            "fallback_narrative": "",
            "default_options": [],
            "narrative_only": narr,
        }
        for i, (t, narr) in enumerate(types_narrative)
    ]


def test_filter_infant_only_narrative_only():
    """age=5 → 只保留 narrative_only=True 的模板."""
    templates = _make_templates(
        ("daily", True),
        ("daily", False),
        ("adventure", False),
        ("daily", True),
    )
    player = {"realm": "凡人", "age": 5, "faction": ""}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert ids == {"t0", "t3"}  # only narrative_only templates


def test_filter_youth_excludes_adventure():
    """age=14 (YOUTH 12-15) → 排除 adventure 类型模板."""
    templates = _make_templates(
        ("daily", False),
        ("adventure", False),
        ("combat", False),
        ("daily", True),
    )
    player = {"realm": "凡人", "age": 14, "faction": ""}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert "t1" not in ids  # adventure excluded
    assert "t0" in ids
    assert "t2" in ids
    assert "t3" in ids


def test_filter_adult_no_additional_filtering():
    """age=20 → 无额外过滤，与原有行为一致."""
    templates = _make_templates(
        ("daily", False),
        ("adventure", False),
        ("combat", False),
        ("daily", True),
    )
    player = {"realm": "凡人", "age": 20, "faction": ""}
    filtered = filter_templates(templates, player)
    ids = {t["id"] for t in filtered}
    assert ids == {"t0", "t1", "t2", "t3"}  # all pass


def test_filter_infant_empty_returns_fallback():
    """age=5 且无 narrative_only 模板 → filter_templates 返回空列表,
    select_event 应返回 FALLBACK_EVENT."""
    templates = _make_templates(
        ("daily", False),
        ("adventure", False),
    )
    player = {"realm": "凡人", "age": 5, "faction": ""}
    filtered = filter_templates(templates, player)
    assert filtered == []
    # Verify select_event falls back correctly
    event = select_event(calculate_weights(filtered, player))
    assert event is FALLBACK_EVENT


def test_weights_youth_factor():
    """age=14 (YOUTH) → calculate_weights 所有权重 ×0.7."""
    templates = _make_templates(
        ("daily", False),
        ("adventure", False),
    )
    player = {"realm": "金丹", "luck": 5, "cultivation": 0, "age": 14, "faction": ""}
    weighted = calculate_weights(templates, player)
    # daily base = 1.0, adventure base = 0.3 + 5*0.05 = 0.55
    # both × 0.7
    assert weighted[0][1] == pytest.approx(0.7)       # daily: 1.0 * 0.7
    assert weighted[1][1] == pytest.approx(0.385)     # adventure: 0.55 * 0.7


def test_weights_adult_no_youth_factor():
    """age=20 → 无 youth factor, 权重不变."""
    templates = _make_templates(
        ("daily", False),
        ("adventure", False),
    )
    player = {"realm": "金丹", "luck": 5, "cultivation": 0, "age": 20, "faction": ""}
    weighted = calculate_weights(templates, player)
    assert weighted[0][1] == pytest.approx(1.0)   # daily: no factor
    assert weighted[1][1] == pytest.approx(0.55)   # adventure: 0.3 + 5*0.05
