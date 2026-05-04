"""Tests for talent card system (Task 5)."""

import random

import pytest

from app.services.talent_service import draw_cards, load_talents, validate_selection


# ---------------------------------------------------------------------------
# load_talents()
# ---------------------------------------------------------------------------


def test_load_talents_returns_20_cards():
    talents = load_talents()
    assert len(talents) == 20


def test_all_talents_have_required_fields():
    talents = load_talents()
    required = {"id", "name", "grade", "rarity", "category", "description", "effects"}
    for t in talents:
        assert required.issubset(t.keys()), f"Card {t.get('id', '?')} missing fields"


def test_all_talent_ids_have_correct_prefix():
    """f01-f06, l01-l06, x01-x04, s01-s03, d01."""
    talents = load_talents()
    prefixes = {"f", "l", "x", "s", "d"}
    for t in talents:
        assert t["id"][0] in prefixes, f"Bad prefix in {t['id']}"


def test_talent_grades_are_valid():
    talents = load_talents()
    valid_grades = {"凡品", "灵品", "玄品", "仙品", "神品"}
    for t in talents:
        assert t["grade"] in valid_grades, f"Bad grade in {t['id']}"


def test_talent_rarity_values():
    """Each card's rarity should be one of the 5 defined values."""
    talents = load_talents()
    valid_rarities = {0.4, 0.3, 0.2, 0.08, 0.02}
    for t in talents:
        assert t["rarity"] in valid_rarities, f"Bad rarity in {t['id']}"


def test_grade_distribution():
    """6 凡品, 6 灵品, 4 玄品, 3 仙品, 1 神品."""
    talents = load_talents()
    counts = {"凡品": 0, "灵品": 0, "玄品": 0, "仙品": 0, "神品": 0}
    for t in talents:
        counts[t["grade"]] += 1
    assert counts == {"凡品": 6, "灵品": 6, "玄品": 4, "仙品": 3, "神品": 1}


def test_grade_and_rarity_match():
    """凡品→0.4, 灵品→0.3, 玄品→0.2, 仙品→0.08, 神品→0.02."""
    grade_rarity = {"凡品": 0.4, "灵品": 0.3, "玄品": 0.2, "仙品": 0.08, "神品": 0.02}
    talents = load_talents()
    for t in talents:
        assert t["rarity"] == grade_rarity[t["grade"]], (
            f"{t['id']} grade={t['grade']} but rarity={t['rarity']}"
        )


def test_all_talents_have_effects_content():
    """effects should have attr_bonuses and modifiers keys, even if empty."""
    talents = load_talents()
    for t in talents:
        effects = t["effects"]
        assert "attr_bonuses" in effects, f"{t['id']} missing attr_bonuses"
        assert "modifiers" in effects, f"{t['id']} missing modifiers"


def test_double_sided_cards_have_positive_and_negative_effects():
    """血祭之契(l06), 天煞孤星(x04), 残缺神魂(s03) are dual."""
    talents = load_talents()
    dual_ids = {"l06", "x04", "s03"}
    for t in talents:
        if t["id"] in dual_ids:
            assert "positive_effects" in t, f"{t['id']} missing positive_effects"
            assert "negative_effects" in t, f"{t['id']} missing negative_effects"
        else:
            assert "positive_effects" not in t, f"{t['id']} should not have positive_effects"
            assert "negative_effects" not in t, f"{t['id']} should not have negative_effects"


def test_blood_pact_specific_effects():
    """血祭之契: positive=突破+25%无需丹, negative=每次突破消耗30%血量."""
    talents = load_talents()
    t = next(x for x in talents if x["id"] == "l06")
    pos = t["positive_effects"]["modifiers"]
    neg = t["negative_effects"]["modifiers"]
    assert pos.get("breakthrough_pill_chance") == 0.25
    assert neg.get("breakthrough_health_cost") == 0.3


def test_doomed_star_specific_effects():
    """天煞孤星: positive=气运+3事件多一选项, negative=情缘关闭NPC关系-50%."""
    talents = load_talents()
    t = next(x for x in talents if x["id"] == "x04")
    pos_attr = t["positive_effects"]["attr_bonuses"]
    pos_mod = t["positive_effects"]["modifiers"]
    neg_mod = t["negative_effects"]["modifiers"]
    assert pos_attr.get("luck") == 3
    assert pos_mod.get("extra_event_option") == 1
    assert neg_mod.get("romance_blocked") is True
    assert neg_mod.get("npc_relation_penalty") == -0.5


def test_broken_soul_specific_effects():
    """残缺神魂: positive=死亡复活一次, negative=悟性-2学习速度-30%."""
    talents = load_talents()
    t = next(x for x in talents if x["id"] == "s03")
    pos_mod = t["positive_effects"]["modifiers"]
    neg_attr = t["negative_effects"]["attr_bonuses"]
    neg_mod = t["negative_effects"]["modifiers"]
    assert pos_mod.get("death_resurrection") == 1
    assert neg_attr.get("comprehension") == -2
    assert neg_mod.get("learning_speed") == -0.3


# ---------------------------------------------------------------------------
# draw_cards()
# ---------------------------------------------------------------------------


def test_draw_cards_default_count():
    drawn = draw_cards()
    assert len(drawn) == 3


def test_draw_cards_custom_count():
    drawn = draw_cards(5)
    assert len(drawn) == 5


def test_draw_cards_returns_valid_talent_dicts():
    talents_map = {t["id"]: t for t in load_talents()}
    drawn = draw_cards(3)
    for c in drawn:
        assert "id" in c
        assert c["id"] in talents_map


def test_draw_cards_no_duplicates_in_single_draw():
    for _ in range(50):
        drawn = draw_cards(3)
        ids = [c["id"] for c in drawn]
        assert len(ids) == len(set(ids)), f"Duplicates in: {ids}"


def test_draw_cards_respects_seed():
    """Same seed should produce same results."""
    random.seed(42)
    first = draw_cards(3)
    random.seed(42)
    second = draw_cards(3)
    assert [c["id"] for c in first] == [c["id"] for c in second]


# ---------------------------------------------------------------------------
# validate_selection()
# ---------------------------------------------------------------------------


def test_validate_selection_valid_returns_true():
    valid, msg = validate_selection(["f01", "l02", "x03"])
    assert valid is True
    assert msg == ""


def test_validate_selection_wrong_count_low():
    valid, msg = validate_selection(["f01", "l02"])
    assert valid is False
    assert "必须选择3张" in msg


def test_validate_selection_wrong_count_high():
    valid, msg = validate_selection(["f01", "l02", "x03", "s01"])
    assert valid is False
    assert "必须选择3张" in msg


def test_validate_selection_invalid_talent_id():
    valid, msg = validate_selection(["f01", "l02", "invalid_id"])
    assert valid is False
    assert "invalid_id" in msg


def test_validate_selection_empty_list():
    valid, msg = validate_selection([])
    assert valid is False
    assert "必须选择3张" in msg


# ---------------------------------------------------------------------------
# Statistical distribution tests
# ---------------------------------------------------------------------------


def test_rarity_distribution_reasonable():
    """Sample 50000 draws, verify grade distribution is within tolerance."""
    random.seed(12345)
    talents_map = {t["id"]: t for t in load_talents()}
    grade_counts = {"凡品": 0, "灵品": 0, "玄品": 0, "仙品": 0, "神品": 0}
    n = 20000  # 20000 draws × 3 cards = 60000 samples
    for _ in range(n):
        drawn = draw_cards(3)
        for c in drawn:
            t = talents_map[c["id"]]
            grade_counts[t["grade"]] += 1

    total = sum(grade_counts.values())
    ratios = {k: v / total for k, v in grade_counts.items()}

    # Allow ±3% tolerance on large samples
    assert abs(ratios["凡品"] - 0.40) < 0.03, f"凡品 ratio {ratios['凡品']:.4f} out of range"
    assert abs(ratios["灵品"] - 0.30) < 0.03, f"灵品 ratio {ratios['灵品']:.4f} out of range"
    assert abs(ratios["玄品"] - 0.20) < 0.02, f"玄品 ratio {ratios['玄品']:.4f} out of range"
    assert abs(ratios["仙品"] - 0.08) < 0.02, f"仙品 ratio {ratios['仙品']:.4f} out of range"
    assert abs(ratios["神品"] - 0.02) < 0.015, f"神品 ratio {ratios['神品']:.4f} out of range"
