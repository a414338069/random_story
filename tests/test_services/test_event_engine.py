"""Tests for event engine (Task 8)."""

import random

import pytest

from app.services.event_engine import (
    FALLBACK_EVENT,
    REALM_TIER_MAP,
    _apply_consequence_scale,
    _get_realm_tier,
    _get_realm_value,
    _safe_format,
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
    """age=5 且无 narrative_only 模板 → filter_templates 自动返回 FALLBACK_EVENT."""
    templates = _make_templates(
        ("daily", False),
        ("adventure", False),
    )
    player = {"realm": "凡人", "age": 5, "faction": ""}
    filtered = filter_templates(templates, player)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "fallback"
    event = select_event(calculate_weights(filtered, player))
    assert event["id"] == "fallback"


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


# ---------------------------------------------------------------------------
# calculate_weights() — talent event_luck_bonus (T8)
# ---------------------------------------------------------------------------


def test_event_weights_with_talent_luck_bonus():
    """event_luck_bonus from talents gets added to adventure event weight."""
    templates = _make_templates(
        ("adventure", False),
        ("daily", False),
    )
    player = {"realm": "金丹", "luck": 0, "cultivation": 0, "age": 20, "faction": ""}

    # 1) Without talents: base formula 0.3 + 0*0.05 = 0.3
    weighted_no_talent = calculate_weights(templates, player)
    assert weighted_no_talent[0][1] == pytest.approx(0.3)
    assert weighted_no_talent[1][1] == pytest.approx(1.0)

    # 2) With l03 (锦鲤命, event_luck_bonus=0.15)
    weighted_l03 = calculate_weights(templates, player, {"talent_ids": ["l03"]})
    assert weighted_l03[0][1] == pytest.approx(0.45)  # 0.3 + 0 + 0.15
    assert weighted_l03[1][1] == pytest.approx(1.0)

    # 3) ctx=None — backward compatible, behaves like no talents
    player2 = {"realm": "金丹", "luck": 5, "cultivation": 0, "age": 20, "faction": ""}
    weighted_none = calculate_weights(templates, player2, None)
    assert weighted_none[0][1] == pytest.approx(0.55)  # 0.3 + 5*0.05

    # 4) ctx with empty talent_ids — no bonus
    weighted_empty = calculate_weights(templates, player2, {"talent_ids": []})
    assert weighted_empty[0][1] == pytest.approx(0.55)

    # 5) ctx without talent_ids key — no bonus (graceful)
    weighted_no_key = calculate_weights(templates, player2, {"other": "value"})
    assert weighted_no_key[0][1] == pytest.approx(0.55)

    # 6) Talent without event_luck_bonus (f03 modifiers={}) — no bonus
    weighted_f03 = calculate_weights(templates, player, {"talent_ids": ["f03"]})
    assert weighted_f03[0][1] == pytest.approx(0.3)

    # 7) Mixed: f03 (no bonus) + l03 (bonus=0.15) = 0.15
    weighted_mixed = calculate_weights(templates, player, {"talent_ids": ["f03", "l03"]})
    assert weighted_mixed[0][1] == pytest.approx(0.45)  # 0.3 + 0 + 0.15


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


# ---------------------------------------------------------------------------
# REALM_TIER_MAP
# ---------------------------------------------------------------------------


def test_realm_tier_map_values():
    """REALM_TIER_MAP 将 order 1-9 映射到正确的层级."""
    assert REALM_TIER_MAP[1] == "低阶"
    assert REALM_TIER_MAP[2] == "低阶"
    assert REALM_TIER_MAP[3] == "低阶"
    assert REALM_TIER_MAP[4] == "中阶"
    assert REALM_TIER_MAP[5] == "中阶"
    assert REALM_TIER_MAP[6] == "中阶"
    assert REALM_TIER_MAP[7] == "高阶"
    assert REALM_TIER_MAP[8] == "高阶"
    assert REALM_TIER_MAP[9] == "高阶"


# ---------------------------------------------------------------------------
# _get_realm_tier()
# ---------------------------------------------------------------------------


def test_get_realm_tier_low():
    """凡人(order=1) → 低阶."""
    assert _get_realm_tier("凡人") == "低阶"
    assert _get_realm_tier("炼气") == "低阶"
    assert _get_realm_tier("筑基") == "低阶"


def test_get_realm_tier_mid():
    """金丹(order=4) → 中阶."""
    assert _get_realm_tier("金丹") == "中阶"
    assert _get_realm_tier("元婴") == "中阶"
    assert _get_realm_tier("化神") == "中阶"


def test_get_realm_tier_high():
    """合体(order=7) → 高阶."""
    assert _get_realm_tier("合体") == "高阶"
    assert _get_realm_tier("大乘") == "高阶"
    assert _get_realm_tier("渡劫飞升") == "高阶"


def test_get_realm_tier_unknown():
    """未知境界返回 None."""
    assert _get_realm_tier("不存在") is None
    assert _get_realm_tier("") is None


# ---------------------------------------------------------------------------
# _get_realm_value()
# ---------------------------------------------------------------------------


def test_get_realm_value_exact_match():
    """精确境界匹配优先."""
    values = {"金丹": "金丹专属文本", "中阶": "中阶通用文本"}
    assert _get_realm_value(values, "金丹") == "金丹专属文本"


def test_get_realm_value_tier_fallback():
    """无精确匹配时回退到层级匹配."""
    values = {"中阶": "中阶通用文本"}
    # 元婴是"中阶"
    assert _get_realm_value(values, "元婴") == "中阶通用文本"


def test_get_realm_value_no_match():
    """无精确匹配也无层级匹配时返回 None."""
    values = {"金丹": "金丹专属文本"}
    assert _get_realm_value(values, "凡人") is None  # 低阶不在 values 中
    assert _get_realm_value({}, "金丹") is None


def test_get_realm_value_empty_dict():
    """空 dict 返回 None."""
    assert _get_realm_value({}, "金丹") is None


def test_get_realm_value_none_values():
    """values 为 None 时返回 None (dict.get 返回 None 时不会报错)."""
    assert _get_realm_value(None, "金丹") is None


# ---------------------------------------------------------------------------
# _apply_consequence_scale()
# ---------------------------------------------------------------------------


def test_apply_consequence_scale_tier_type():
    """scale_config type=tier → 按层级缩放."""
    options = [
        {
            "id": "opt1",
            "text": "修炼",
            "consequences": {"cultivation_gain": 100, "spirit_stones_gain": 50},
        },
    ]
    scale_config = {"type": "tier", "低阶": 1.0, "中阶": 1.5, "高阶": 2.0}
    # 元婴是"中阶" → factor=1.5
    result = _apply_consequence_scale(options, scale_config, "元婴")

    assert result is not options  # deep copy
    assert result[0]["consequences"]["cultivation_gain"] == 150.0
    assert result[0]["consequences"]["spirit_stones_gain"] == 75.0


def test_apply_consequence_scale_realm_type():
    """scale_config type=realm → 按精确境界缩放."""
    options = [
        {
            "id": "opt1",
            "text": "突破",
            "consequences": {"cultivation_gain": 200},
        },
    ]
    scale_config = {"type": "realm", "金丹": 1.5}
    result = _apply_consequence_scale(options, scale_config, "金丹")
    assert result[0]["consequences"]["cultivation_gain"] == 300.0


def test_apply_consequence_scale_no_match():
    """scale_config 中无匹配境界 → factor=1.0 (不变)."""
    options = [
        {
            "id": "opt1",
            "text": "修炼",
            "consequences": {"cultivation_gain": 100},
        },
    ]
    scale_config = {"type": "realm", "金丹": 1.5}
    result = _apply_consequence_scale(options, scale_config, "凡人")
    assert result[0]["consequences"]["cultivation_gain"] == 100.0


def test_apply_consequence_scale_empty_options():
    """空 options → 返回空列表."""
    result = _apply_consequence_scale([], {"type": "tier", "中阶": 2.0}, "金丹")
    assert result == []


def test_apply_consequence_scale_empty_scale_config():
    """空 scale_config → 返回深拷贝."""
    options = [{"id": "opt1", "text": "test", "consequences": {"cultivation_gain": 5}}]
    result = _apply_consequence_scale(options, {}, "金丹")
    assert result is not options
    assert result[0]["consequences"]["cultivation_gain"] == 5


def test_apply_consequence_scale_non_numeric_preserved():
    """非数值字段 (如 age_advance:True) 保持不变."""
    options = [
        {
            "id": "opt1",
            "text": "修炼",
            "consequences": {"cultivation_gain": 100, "age_advance": True},
        },
    ]
    scale_config = {"type": "realm", "金丹": 2.0}
    result = _apply_consequence_scale(options, scale_config, "金丹")
    assert result[0]["consequences"]["cultivation_gain"] == 200.0
    assert result[0]["consequences"]["age_advance"] is True


def test_apply_consequence_scale_does_not_mutate_original():
    """原始 options 不被修改."""
    options = [
        {"id": "opt1", "consequences": {"cultivation_gain": 100}},
    ]
    original_val = options[0]["consequences"]["cultivation_gain"]
    _apply_consequence_scale(options, {"type": "realm", "金丹": 2.0}, "金丹")
    assert options[0]["consequences"]["cultivation_gain"] == original_val


# ---------------------------------------------------------------------------
# _safe_format() / _SafeFormatDict
# ---------------------------------------------------------------------------


def test_safe_format_normal():
    """正常占位符应被替换."""
    assert _safe_format("你已{age}岁", age=500) == "你已500岁"


def test_safe_format_missing_key():
    """未知占位符保留原始形式."""
    assert _safe_format("你已{age}岁，{unknown}", age=500) == "你已500岁，{unknown}"


def test_safe_format_no_args():
    """无占位符的文本原样返回."""
    assert _safe_format("你在山中修炼了一天。") == "你在山中修炼了一天。"


def test_safe_format_multiple_missing():
    """多个未知占位符全部保留."""
    assert _safe_format("{a} and {b} and {c}", x=1) == "{a} and {b} and {c}"


# ---------------------------------------------------------------------------
# build_event_context() — realm differentiation
# ---------------------------------------------------------------------------


def test_build_event_context_realm_prompt_templates():
    """realm_prompt_templates 按境界覆盖 prompt."""
    template = {
        "id": "test_realm_prompt",
        "type": "daily",
        "title": "测试",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999, "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "默认叙事",
        "fallback_narrative": "",
        "default_options": [],
        "realm_prompt_templates": {
            "金丹": "金丹专属叙事 - realm={realm}",
            "中阶": "中阶通用叙事",
        },
    }
    player = {"realm": "金丹", "age": 500}
    ctx = build_event_context(template, player)
    assert "金丹专属叙事 - realm=金丹" in ctx["prompt"]


def test_build_event_context_realm_prompt_tier_fallback():
    """realm_prompt_templates 中无精确匹配时使用层级回退."""
    template = {
        "id": "test_realm_prompt",
        "type": "daily",
        "title": "测试",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999, "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "默认叙事",
        "fallback_narrative": "",
        "default_options": [],
        "realm_prompt_templates": {
            "中阶": "中阶通用叙事 - {realm_variant}",
        },
    }
    player = {"realm": "元婴", "age": 800}
    ctx = build_event_context(template, player)
    assert "中阶通用叙事 - 中阶" in ctx["prompt"]


def test_build_event_context_realm_narratives():
    """realm_narratives 按境界覆盖 fallback_narrative."""
    template = {
        "id": "test_realm_narrative",
        "type": "daily",
        "title": "测试",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999, "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "",
        "fallback_narrative": "默认叙事",
        "default_options": [],
        "realm_narratives": {
            "高阶": "高阶专属叙事",
        },
    }
    player = {"realm": "合体", "age": 2000}
    ctx = build_event_context(template, player)
    assert ctx["fallback_narrative"] == "高阶专属叙事"


def test_build_event_context_realm_default_options():
    """realm_default_options 按境界覆盖 default_options."""
    realm_opts = [
        {"id": "realm_opt", "text": "境界专属选项", "consequences": {"cultivation_gain": 50}},
    ]
    template = {
        "id": "test_realm_opts",
        "type": "daily",
        "title": "测试",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999, "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "",
        "fallback_narrative": "",
        "default_options": [
            {"id": "default_opt", "text": "默认选项", "consequences": {"cultivation_gain": 5}},
        ],
        "realm_default_options": {
            "金丹": realm_opts,
        },
    }
    player = {"realm": "金丹", "age": 300}
    ctx = build_event_context(template, player)
    assert ctx["default_options"] == realm_opts


def test_build_event_context_realm_scale():
    """realm_scale 对 consequences 数值字段进行缩放."""
    template = {
        "id": "test_realm_scale",
        "type": "daily",
        "title": "测试",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999, "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "",
        "fallback_narrative": "",
        "default_options": [
            {"id": "opt1", "text": "修炼", "consequences": {"cultivation_gain": 100}},
        ],
        "realm_scale": {"type": "tier", "低阶": 1.0, "中阶": 2.0, "高阶": 3.0},
    }
    player = {"realm": "金丹", "age": 500}  # 金丹=中阶 → factor=2.0
    ctx = build_event_context(template, player)
    assert ctx["default_options"][0]["consequences"]["cultivation_gain"] == 200.0


def test_build_event_context_realm_variable():
    """{realm_variant} 格式化变量可用."""
    template = {
        "id": "test_realm_variant",
        "type": "daily",
        "title": "测试",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999, "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "你处于{realm_variant}境界",
        "fallback_narrative": "",
        "default_options": [],
    }
    player = {"realm": "金丹", "age": 500}
    ctx = build_event_context(template, player)
    assert "中阶" in ctx["prompt"]


def test_build_event_context_backward_compatible():
    """无 realm_* 字段的模板行为完全不变."""
    template = {
        "id": "test_backward",
        "type": "daily",
        "title": "测试",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999, "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "你已{age}岁",
        "fallback_narrative": "修为增长",
        "default_options": [
            {"id": "opt1", "text": "修炼", "consequences": {"cultivation_gain": 5}},
        ],
    }
    player = {"realm": "金丹", "age": 500}
    ctx = build_event_context(template, player)
    assert ctx["prompt"] == "你已500岁"
    assert ctx["fallback_narrative"] == "修为增长"
    assert ctx["default_options"] == template["default_options"]
    assert ctx["player"] == player


def test_build_event_context_safe_format_unknown_keys():
    """prompt_template 中的未知占位符被保留而非抛异常."""
    template = {
        "id": "test_safe_format",
        "type": "daily",
        "title": "测试",
        "trigger_conditions": {
            "min_realm": "凡人", "max_realm": "渡劫飞升",
            "min_age": 0, "max_age": 9999, "required_faction": None,
        },
        "weight": 1.0,
        "prompt_template": "{realm}境界，{unknown_key}未知",
        "fallback_narrative": "",
        "default_options": [],
    }
    player = {"realm": "金丹", "age": 500}
    ctx = build_event_context(template, player)
    assert "金丹境界" in ctx["prompt"]
    assert "{unknown_key}未知" in ctx["prompt"]


# ---------------------------------------------------------------------------
# trigger_tags filtering (T12) — filter_templates()
# ---------------------------------------------------------------------------


def _make_tag_template(
    tid: str, require_all=None, require_any=None, block=None, **overrides
) -> dict:
    """Build a synthetic template with trigger_tags."""
    return {
        "id": tid,
        "type": "daily",
        "title": f"template {tid}",
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
        "trigger_tags": {
            "require_all": require_all or [],
            "require_any": require_any or [],
            "block": block or [],
        },
        **overrides,
    }


def _make_tagset(keys: list[str]) -> "TagSet":
    from app.models.tags import Tag, TagCategory, TagSet

    tags = []
    for key in keys:
        tags.append(Tag(category=TagCategory.IDENTITY, key=key, value=key))
    return TagSet(tags=tags)


class TestTriggerTagsFiltering:
    """Tests for trigger_tags-based filtering in filter_templates()."""

    def test_no_tags_passes_through(self):
        """Templates with empty trigger_tags pass through regardless of player tags."""
        t1 = _make_tag_template("t1")
        t2 = _make_tag_template("t2")
        player = {"realm": "凡人", "age": 20, "faction": ""}
        result = filter_templates([t1, t2], player)
        assert {t["id"] for t in result} == {"t1", "t2"}

    def test_no_player_tags_passes_through(self):
        """When player has no tags, all templates pass through (no tag filtering)."""
        t1 = _make_tag_template("t1", require_all=["identity:test"])
        t2 = _make_tag_template("t2")
        player = {"realm": "凡人", "age": 20, "faction": ""}
        result = filter_templates([t1, t2], player)
        assert {t["id"] for t in result} == {"t1", "t2"}

    def test_require_all_single_match(self):
        """require_all with a single key: template passes when player has the tag."""
        t1 = _make_tag_template("t1", require_all=["identity:青云门"])
        t2 = _make_tag_template("t2")
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["identity:青云门"]),
        }
        result = filter_templates([t1, t2], player)
        ids = {t["id"] for t in result}
        assert "t1" in ids
        assert "t2" in ids

    def test_require_all_single_mismatch(self):
        """require_all with missing tag → template excluded."""
        t1 = _make_tag_template("t1", require_all=["identity:万剑山庄"])
        t2 = _make_tag_template("t2")
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["identity:青云门"]),
        }
        result = filter_templates([t1, t2], player)
        ids = {t["id"] for t in result}
        assert "t1" not in ids
        assert "t2" in ids

    def test_require_all_multiple_all_present(self):
        """require_all with multiple keys: ALL must be present."""
        t1 = _make_tag_template("t1", require_all=["identity:青云门", "skill:剑法入门"])
        t2 = _make_tag_template("t2")
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["identity:青云门", "skill:剑法入门"]),
        }
        result = filter_templates([t1, t2], player)
        ids = {t["id"] for t in result}
        assert "t1" in ids

    def test_require_all_multiple_partial(self):
        """require_all with multiple keys: missing one → excluded."""
        t1 = _make_tag_template(
            "t1", require_all=["identity:青云门", "skill:剑法精通"]
        )
        t2 = _make_tag_template("t2")
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["identity:青云门", "skill:剑法入门"]),
        }
        result = filter_templates([t1, t2], player)
        ids = {t["id"] for t in result}
        assert "t1" not in ids  # missing "skill:剑法精通"

    def test_require_any_single_match(self):
        """require_any: at least one of the listed tags must exist."""
        t1 = _make_tag_template("t1", require_any=["skill:剑法入门", "skill:剑法精通"])
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["skill:剑法入门"]),
        }
        result = filter_templates([t1], player)
        ids = {t["id"] for t in result}
        assert "t1" in ids

    def test_require_any_none_match(self):
        """require_any: none present → excluded."""
        t1 = _make_tag_template("t1", require_any=["skill:剑法入门", "skill:剑法精通"])
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["skill:拳法入门"]),
        }
        result = filter_templates([t1], player)
        assert result == [FALLBACK_EVENT.copy()]

    def test_require_any_multiple_any_one_matches(self):
        """require_any with multiple keys: at least one match passes."""
        t1 = _make_tag_template(
            "t1", require_any=["skill:剑法入门", "skill:炼丹入门", "skill:符箓入门"]
        )
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["skill:炼丹入门"]),
        }
        result = filter_templates([t1], player)
        ids = {t["id"] for t in result}
        assert "t1" in ids

    def test_block_single_match(self):
        """block: any matching tag → template excluded."""
        t1 = _make_tag_template("t1", block=["state:injured"])
        t2 = _make_tag_template("t2")
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["state:injured"]),
        }
        result = filter_templates([t1, t2], player)
        ids = {t["id"] for t in result}
        assert "t1" not in ids
        assert "t2" in ids

    def test_block_no_match(self):
        """block tag not present on player → template passes."""
        t1 = _make_tag_template("t1", block=["state:injured"])
        t2 = _make_tag_template("t2")
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["state:blessed"]),
        }
        result = filter_templates([t1, t2], player)
        ids = {t["id"] for t in result}
        assert "t1" in ids

    def test_block_multiple_one_matches(self):
        """block with multiple keys: any single match → excluded."""
        t1 = _make_tag_template(
            "t1", block=["state:injured", "state:poisoned", "state:cursed"]
        )
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["state:poisoned"]),
        }
        result = filter_templates([t1], player)
        assert result == [FALLBACK_EVENT.copy()]

    def test_combined_require_all_and_block(self):
        """require_all passes AND no block match → template included."""
        t1 = _make_tag_template(
            "t1",
            require_all=["identity:青云门"],
            block=["state:injured"],
        )
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["identity:青云门"]),
        }
        result = filter_templates([t1], player)
        ids = {t["id"] for t in result}
        assert "t1" in ids

    def test_combined_require_all_passes_but_blocked(self):
        """require_all passes but block matches → excluded."""
        t1 = _make_tag_template(
            "t1",
            require_all=["identity:青云门"],
            block=["state:injured"],
        )
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["identity:青云门", "state:injured"]),
        }
        result = filter_templates([t1], player)
        assert result == [FALLBACK_EVENT.copy()]

    def test_combined_require_all_and_require_any(self):
        """Both require_all and require_any must pass."""
        t1 = _make_tag_template(
            "t1",
            require_all=["identity:青云门"],
            require_any=["skill:剑法入门", "skill:剑法精通"],
        )
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["identity:青云门", "skill:剑法精通"]),
        }
        result = filter_templates([t1], player)
        ids = {t["id"] for t in result}
        assert "t1" in ids

    def test_fallback_when_all_filtered_by_tags(self):
        """When all templates are excluded by trigger_tags, return FALLBACK_EVENT."""
        t1 = _make_tag_template("t1", require_all=["identity:nonexistent"])
        t2 = _make_tag_template("t2", block=["state:injured"])
        player = {
            "realm": "凡人",
            "age": 20,
            "faction": "",
            "tags": _make_tagset(["state:injured"]),
        }
        result = filter_templates([t1, t2], player)
        assert result == [FALLBACK_EVENT.copy()]

    def test_youth_filtering_preserved_with_tags(self):
        """Life-stage filtering still works alongside trigger_tags filtering."""
        t1 = _make_tag_template("t1", require_all=["identity:青云门"])
        t1["type"] = "adventure"
        t2 = _make_tag_template("t2")
        player = {
            "realm": "凡人",
            "age": 14,
            "faction": "",
            "tags": _make_tagset(["identity:青云门"]),
        }
        result = filter_templates([t1, t2], player)
        ids = {t["id"] for t in result}
        assert "t1" not in ids  # excluded due to YOUTH adventure filter


# ---------------------------------------------------------------------------
# trigger_tags — calculate_weights() tag relevance bonus
# ---------------------------------------------------------------------------


class TestTriggerTagsWeights:
    """Tests for tag relevance bonus in calculate_weights()."""

    def test_tag_relevance_bonus_single_tag(self):
        """One matched require_all tag → +0.1 weight bonus."""
        t1 = _make_tag_template("t1", require_all=["identity:青云门"])
        player = {
            "realm": "金丹",
            "luck": 5,
            "cultivation": 0,
            "age": 500,
            "faction": "",
            "tags": _make_tagset(["identity:青云门"]),
        }
        weighted = calculate_weights([t1], player)
        # daily base = 1.0, +0.1 bonus = 1.1
        assert weighted[0][1] == pytest.approx(1.1)

    def test_tag_relevance_bonus_multiple_tags(self):
        """Two matched require_all tags → +0.2 weight bonus."""
        t1 = _make_tag_template(
            "t1", require_all=["identity:青云门", "skill:剑法精通"]
        )
        player = {
            "realm": "金丹",
            "luck": 5,
            "cultivation": 0,
            "age": 500,
            "faction": "",
            "tags": _make_tagset(["identity:青云门", "skill:剑法精通"]),
        }
        weighted = calculate_weights([t1], player)
        # daily base = 1.0, +0.2 bonus = 1.2
        assert weighted[0][1] == pytest.approx(1.2)

    def test_tag_relevance_bonus_partial_match(self):
        """Only matched tags count; unmatched ones give no bonus."""
        t1 = _make_tag_template(
            "t1", require_all=["identity:青云门", "skill:剑法精通"]
        )
        player = {
            "realm": "金丹",
            "luck": 5,
            "cultivation": 0,
            "age": 500,
            "faction": "",
            "tags": _make_tagset(["identity:青云门"]),
        }
        weighted = calculate_weights([t1], player)
        # daily base = 1.0, +0.1 bonus (only 1 matched)
        assert weighted[0][1] == pytest.approx(1.1)

    def test_tag_relevance_no_bonus_no_tags(self):
        """No trigger_tags on template → no bonus."""
        t1 = {
            "id": "t1",
            "type": "daily",
            "title": "test",
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
            "trigger_tags": {"require_all": [], "require_any": [], "block": []},
        }
        player = {
            "realm": "金丹",
            "luck": 5,
            "cultivation": 0,
            "age": 500,
            "faction": "",
            "tags": _make_tagset(["identity:青云门"]),
        }
        weighted = calculate_weights([t1], player)
        assert weighted[0][1] == pytest.approx(1.0)

    def test_tag_relevance_no_bonus_no_player_tags(self):
        """No player tags → no bonus."""
        t1 = _make_tag_template("t1", require_all=["identity:青云门"])
        player = {
            "realm": "金丹",
            "luck": 5,
            "cultivation": 0,
            "age": 500,
            "faction": "",
        }
        weighted = calculate_weights([t1], player)
        assert weighted[0][1] == pytest.approx(1.0)

    def test_tag_bonus_with_youth_factor(self):
        """Tag bonus is added AFTER youth factor, not diluted by it."""
        t1 = _make_tag_template("t1", require_all=["identity:青云门"])
        player = {
            "realm": "金丹",
            "luck": 5,
            "cultivation": 0,
            "age": 14,
            "faction": "",
            "tags": _make_tagset(["identity:青云门"]),
        }
        weighted = calculate_weights([t1], player)
        # daily base = 1.0 * 0.7 = 0.7, +0.1 bonus = 0.8
        assert weighted[0][1] == pytest.approx(0.8)
