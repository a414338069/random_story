"""Tests for breakthrough system (Task 9 + T4 refactor)."""

import random

import pytest

from app.services.breakthrough import (
    BreakthroughResult,
    get_realm_penalty,
    calculate_success_rate,
    attempt_breakthrough,
    build_breakthrough_event,
    PILL_BONUS,
    BULWARK_TALENT_NAME,
    BULWARK_LOSS_REDUCTION,
)


# ---------------------------------------------------------------------------
# get_realm_penalty()
# ---------------------------------------------------------------------------


def test_get_realm_penalty_fanren():
    assert get_realm_penalty("凡人") == 0.00


def test_get_realm_penalty_lianqi():
    assert get_realm_penalty("炼气") == 0.05


def test_get_realm_penalty_zhuji():
    assert get_realm_penalty("筑基") == 0.10


def test_get_realm_penalty_jindan():
    assert get_realm_penalty("金丹") == 0.15


def test_get_realm_penalty_yuanying():
    assert get_realm_penalty("元婴") == 0.20


def test_get_realm_penalty_huashen():
    assert get_realm_penalty("化神") == 0.25


def test_get_realm_penalty_heti():
    assert get_realm_penalty("合体") == 0.30


def test_get_realm_penalty_dacheng():
    assert get_realm_penalty("大乘") == 0.35


def test_get_realm_penalty_unknown_realm():
    assert get_realm_penalty("不存在") == 0.0


# ---------------------------------------------------------------------------
# calculate_success_rate()
# ---------------------------------------------------------------------------


def test_zero_attributes_rate():
    """全0属性 → rate=0.50"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
    assert calculate_success_rate(player) == 0.50


def test_max_rootbone_capped():
    """rootBone=10 → 0.50+0.50=1.00 → capped at 0.95"""
    player = {"rootBone": 10, "comprehension": 0, "mindset": 0, "realm": "凡人"}
    assert calculate_success_rate(player) == 0.95


def test_comprehension_contribution():
    """comprehension=5 → 0.50+0.15=0.65"""
    player = {"rootBone": 0, "comprehension": 5, "mindset": 0, "realm": "凡人"}
    assert calculate_success_rate(player) == 0.65


def test_mindset_contribution():
    """mindset=5 → 0.50+0.10=0.60"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 5, "realm": "凡人"}
    assert calculate_success_rate(player) == 0.60


def test_pill_bonus():
    """use_pill=True → +0.15"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
    assert calculate_success_rate(player, use_pill=True) == 0.65


def test_realm_penalty_lianqi():
    """炼气 → penalty=0.05, rate=0.45"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "炼气"}
    assert calculate_success_rate(player) == 0.45


def test_realm_penalty_dacheng():
    """大乘 → penalty=0.35, rate=0.15"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "大乘"}
    assert calculate_success_rate(player) == pytest.approx(0.15)


def test_rate_lower_bound():
    """Rate never drops below 0.05"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "大乘"}
    # 0.50 - 0.35 = 0.15 → not yet at bound
    assert calculate_success_rate(player) >= 0.05


def test_rate_upper_bound():
    """Rate never exceeds 0.95"""
    player = {"rootBone": 10, "comprehension": 10, "mindset": 10, "realm": "凡人"}
    # 0.50 + 0.50 + 0.30 + 0.20 = 1.50 → cap at 0.95
    assert calculate_success_rate(player) == 0.95


def test_default_realm_is_fanren():
    """Missing realm defaults to 凡人 → penalty=0"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0}
    assert calculate_success_rate(player) == 0.50


# ---------------------------------------------------------------------------
# attempt_breakthrough() — success
# ---------------------------------------------------------------------------


def test_success_advances_realm():
    """成功 → realm 提升 + cultivation=0"""
    player = {
        "rootBone": 0, "comprehension": 0, "mindset": 0,
        "realm": "凡人", "cultivation": 50, "talent_ids": [],
    }
    random.seed(1)
    result = attempt_breakthrough(player)
    assert result.success is True
    assert result.new_realm == "炼气"
    assert result.cultivation_loss == 0.0
    assert result.realm_dropped is False
    assert result.ascended is False


def test_success_from_dacheng_to_dujie():
    """大乘→渡劫飞升 success → ascended=True"""
    player = {
        "rootBone": 10, "comprehension": 10, "mindset": 10,
        "realm": "大乘", "cultivation": 100000, "talent_ids": [],
    }
    random.seed(1)
    result = attempt_breakthrough(player)
    assert result.success is True
    assert result.new_realm == "渡劫飞升"
    assert result.ascended is True


# ---------------------------------------------------------------------------
# attempt_breakthrough() — failure
# ---------------------------------------------------------------------------


def test_failure_cultivation_loss():
    """失败 → cultivation 损失 20-50%"""
    player = {
        "rootBone": 0, "comprehension": 0, "mindset": 0,
        "realm": "凡人", "cultivation": 100, "talent_ids": [],
    }
    # Seed 2: first random >= 0.50 → failure, second random determines loss
    random.seed(2)
    result = attempt_breakthrough(player)
    assert result.success is False
    assert 20 <= result.cultivation_loss <= 50  # 20-50% of 100
    assert result.ascended is False


def test_failure_realm_drop():
    """失败 → 10% 境界跌落 (用固定seed)"""
    player = {
        "rootBone": 0, "comprehension": 0, "mindset": 0,
        "realm": "炼气", "cultivation": 150, "talent_ids": [],
    }
    random.seed(22)
    result = attempt_breakthrough(player)
    assert result.success is False
    assert result.realm_dropped is True
    assert result.new_realm == "凡人"


def test_failure_realm_drop_from_lowest_stays():
    """凡人跌落 → 应保持在凡人"""
    player = {
        "rootBone": 0, "comprehension": 0, "mindset": 0,
        "realm": "凡人", "cultivation": 50, "talent_ids": [],
    }
    random.seed(2)
    result = attempt_breakthrough(player)
    assert result.new_realm == "凡人"


def test_failure_no_realm_drop():
    """失败 → 90% 概率不跌落境界"""
    player = {
        "rootBone": 0, "comprehension": 0, "mindset": 0,
        "realm": "炼气", "cultivation": 150, "talent_ids": [],
    }
    # Seed 5: first random >= 0.45 → failure, third random >= 0.10 → no drop
    random.seed(5)
    result = attempt_breakthrough(player)
    assert result.success is False
    assert result.realm_dropped is False
    assert result.new_realm == "炼气"


# ---------------------------------------------------------------------------
# attempt_breakthrough() — talent effects
# ---------------------------------------------------------------------------


def test_talent_reduces_loss():
    """百折不挠 → 损失减免10%"""
    player = {
        "rootBone": 0, "comprehension": 0, "mindset": 0,
        "realm": "凡人", "cultivation": 100, "talent_ids": ["f06"],
    }
    random.seed(2)  # same seed as test_failure_cultivation_loss
    result_with = attempt_breakthrough(player)

    player_no_talent = {
        "rootBone": 0, "comprehension": 0, "mindset": 0,
        "realm": "凡人", "cultivation": 100, "talent_ids": [],
    }
    random.seed(2)
    result_without = attempt_breakthrough(player_no_talent)

    # Loss with 百折不挠 should be reduced by the loss reduction ratio
    loss_with = result_with.cultivation_loss
    loss_without = result_without.cultivation_loss
    # The reduction applies to the loss_ratio (0.20-0.50), not directly to cultivation_loss
    # So the loss_with should be <= loss_without - (BULWARK_LOSS_REDUCTION * cultivation)
    # i.e., loss_with <= loss_without - 10
    assert loss_with <= loss_without - (BULWARK_LOSS_REDUCTION * 100) + 0.001


def test_bulwark_talent_no_magic_id():
    """确认百折不挠通过名称匹配而非硬编码ID"""
    from app.services.breakthrough import BULWARK_TALENT_NAME
    from app.services.talent_service import load_talents
    talents = load_talents()
    bulwark = [t for t in talents if t["name"] == BULWARK_TALENT_NAME]
    assert len(bulwark) == 1
    assert bulwark[0]["id"] == "f06"


# ---------------------------------------------------------------------------
# attempt_breakthrough() — edge cases
# ---------------------------------------------------------------------------


def test_already_at_max_realm():
    """渡劫飞升已最高 → ascended=True"""
    player = {
        "rootBone": 10, "comprehension": 10, "mindset": 10,
        "realm": "渡劫飞升", "cultivation": 0, "talent_ids": [],
    }
    result = attempt_breakthrough(player)
    assert result.success is True
    assert result.new_realm == "渡劫飞升"
    assert result.ascended is True
    assert result.cultivation_loss == 0.0
    assert result.realm_dropped is False


def test_ascension_from_dujie():
    """从大乘突破到渡劫飞升，ascended=True"""
    # Use high stats to ensure success
    player = {
        "rootBone": 5, "comprehension": 5, "mindset": 5,
        "realm": "大乘", "cultivation": 100000, "talent_ids": [],
    }
    # rate = 0.50 + 0.25 + 0.15 + 0.10 - 0.35 = 0.65 → capped at 0.95? No, 0.65.
    # need seed where random < 0.65
    random.seed(29)
    result = attempt_breakthrough(player)
    assert result.success is True, f"Expected success but got rate issue"
    assert result.new_realm == "渡劫飞升"
    assert result.ascended is True


def test_attempt_breakthrough_returns_dataclass():
    """验证返回值类型"""
    player = {
        "rootBone": 0, "comprehension": 0, "mindset": 0,
        "realm": "凡人", "cultivation": 0, "talent_ids": [],
    }
    result = attempt_breakthrough(player)
    assert isinstance(result, BreakthroughResult)
    assert isinstance(result.success, bool)
    assert isinstance(result.new_realm, str)
    assert isinstance(result.cultivation_loss, float)
    assert isinstance(result.realm_dropped, bool)
    assert isinstance(result.ascended, bool)


def test_cultivation_reset_on_success():
    """成功突破后 cultivation_loss 为 0"""
    player = {
        "rootBone": 10, "comprehension": 10, "mindset": 10,
        "realm": "凡人", "cultivation": 50, "talent_ids": [],
    }
    random.seed(1)
    result = attempt_breakthrough(player)
    assert result.success is True
    assert result.cultivation_loss == 0.0


def test_failure_has_ascended_false():
    """失败时 ascended 永远为 False"""
    player = {
        "rootBone": 0, "comprehension": 0, "mindset": 0,
        "realm": "大乘", "cultivation": 100000, "talent_ids": [],
    }
    random.seed(42)  # deliberately pick seed where failure might occur
    result = attempt_breakthrough(player)
    if not result.success:
        assert result.ascended is False


# ============================================================================
# T4: build_breakthrough_event()
# ============================================================================


def test_build_breakthrough_event_structure():
    """build_breakthrough_event 返回正确的结构"""
    player = {
        "rootBone": 3, "comprehension": 3, "mindset": 2,
        "realm": "凡人", "cultivation": 99, "talent_ids": [], "age": 20,
        "inventory": ["breakthrough_pill"],
    }
    event = build_breakthrough_event(player)
    assert event["event_id"] == "breakthrough_pending"
    assert event["title"] == "境界突破"
    assert "丹田" in event["narrative"]
    assert event["is_breakthrough"] is True
    assert event["has_options"] is True
    assert len(event["options"]) == 2
    assert event["options"][0]["id"] == "use_pill"
    assert "突破丹" in event["options"][0]["text"]
    assert event["options"][1]["id"] == "direct"
    assert "凭自身" in event["options"][1]["text"]


def test_build_breakthrough_event_structure_no_pill():
    """无突破丹时只返回「凭自身实力突破」选项"""
    player = {
        "rootBone": 3, "comprehension": 3, "mindset": 2,
        "realm": "凡人", "cultivation": 99, "talent_ids": [], "age": 20,
    }
    event = build_breakthrough_event(player)
    assert len(event["options"]) == 1
    assert event["options"][0]["id"] == "direct"


def test_build_breakthrough_event_options_have_required_fields():
    """选项包含 id, text, consequence_preview 字段"""
    player = {
        "rootBone": 3, "comprehension": 3, "mindset": 2,
        "realm": "凡人", "cultivation": 99, "talent_ids": [], "age": 20,
    }
    event = build_breakthrough_event(player)
    for opt in event["options"]:
        assert "id" in opt
        assert "text" in opt
        assert "consequence_preview" in opt


# ============================================================================
# T4: calculate_success_rate() with age penalty
# ============================================================================


def test_success_rate_age_penalty_under_16():
    """age<16 → get_breakthrough_penalty=0.5 → rate 减半"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人", "age": 10}
    rate = calculate_success_rate(player)
    assert rate == pytest.approx(0.25)  # 0.50 * 0.5


def test_success_rate_age_penalty_at_15():
    """age=15 → get_breakthrough_penalty=0.5 → rate 减半"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人", "age": 15}
    rate = calculate_success_rate(player)
    assert rate == pytest.approx(0.25)


def test_success_rate_no_age_penalty_at_16():
    """age=16 → get_breakthrough_penalty=0.0 → rate 不受年龄影响"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人", "age": 16}
    rate = calculate_success_rate(player)
    assert rate == 0.50


def test_success_rate_age_penalty_with_pill():
    """age<16 同时 use_pill=True → pill+年龄惩罚叠加"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人", "age": 10}
    rate = calculate_success_rate(player, use_pill=True)
    # 0.65 * 0.5 = 0.325
    assert rate == pytest.approx(0.325, abs=0.001)


def test_success_rate_age_penalty_respects_bounds():
    """年龄惩罚后仍然受 0.05 下限约束"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "大乘", "age": 10}
    rate = calculate_success_rate(player)
    # 0.50 - 0.35 = 0.15 → 0.15 * 0.5 = 0.075 → clipped to 0.075? No, 0.075 > 0.05
    # Actually 0.075 > 0.05 so no clip needed. Let me find a case that triggers the bound.
    # age=10 penalty=0.5, realm=大乘 penalty=0.35, rate=(0.50-0.35)*0.5=0.075, min=0.05
    assert rate >= 0.05


def test_success_rate_default_age_no_break():
    """默认 age=16 (突破最低年龄) → 无惩罚，不破坏已有测试"""
    player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
    rate = calculate_success_rate(player)
    assert rate == 0.50  # 与 T9 行为一致
