"""Tests for context_engine — scenario pool determination and template matching."""

import pytest

from app.models.tags import Tag, TagCategory, TagSet
from app.services.context_engine import determine_scenario_pool, match_scenarios


def _make_tagset(*tags: Tag) -> TagSet:
    ts = TagSet()
    for t in tags:
        ts.add(t)
    return ts


# ══════════════════════════════════════════════════════════════════════════════
# determine_scenario_pool — base cases
# ══════════════════════════════════════════════════════════════════════════════


def test_empty_tags_returns_only_generic_daily():
    scenarios = determine_scenario_pool(None, {"age": 20})
    assert scenarios == ["generic_daily"]


def test_empty_tagset_returns_only_generic_daily():
    ts = TagSet()
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert scenarios == ["generic_daily"]


def test_no_player_state_returns_only_generic_daily():
    ts = TagSet()
    scenarios = determine_scenario_pool(ts, None)
    assert scenarios == ["generic_daily"]


def test_generic_daily_always_first():
    ts = _make_tagset(
        Tag(category=TagCategory.IDENTITY, key="faction", value="门派=万剑山庄"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert scenarios[0] == "generic_daily"


# ══════════════════════════════════════════════════════════════════════════════
# determine_scenario_pool — faction identity
# ══════════════════════════════════════════════════════════════════════════════


def test_faction_tag_adds_faction_scenarios():
    ts = _make_tagset(
        Tag(category=TagCategory.IDENTITY, key="faction", value="门派=万剑山庄"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "faction_万剑山庄" in scenarios
    assert "faction_life" in scenarios


def test_faction_tag_without_equals_in_value():
    ts = _make_tagset(
        Tag(category=TagCategory.IDENTITY, key="faction", value="散修"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "faction_散修" in scenarios
    assert "faction_life" in scenarios


def test_faction_tag_age_under_21_no_senior():
    ts = _make_tagset(
        Tag(category=TagCategory.IDENTITY, key="faction", value="门派=逍遥派"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 16})
    assert "faction_逍遥派" in scenarios
    assert "faction_life" in scenarios
    assert "faction_senior" not in scenarios


def test_faction_tag_age_21_adds_senior():
    ts = _make_tagset(
        Tag(category=TagCategory.IDENTITY, key="faction", value="门派=逍遥派"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 21})
    assert "faction_senior" in scenarios


def test_faction_tag_age_50_adds_senior():
    ts = _make_tagset(
        Tag(category=TagCategory.IDENTITY, key="faction", value="门派=金刚寺"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 50})
    assert "faction_金刚寺" in scenarios
    assert "faction_senior" in scenarios


# ══════════════════════════════════════════════════════════════════════════════
# determine_scenario_pool — skills
# ══════════════════════════════════════════════════════════════════════════════


def test_skill_tags_add_has_technique():
    ts = _make_tagset(
        Tag(category=TagCategory.SKILL, key="tech_万剑诀", value="功法=万剑诀"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "has_technique" in scenarios


def test_multiple_skill_tags_still_single_has_technique():
    ts = _make_tagset(
        Tag(category=TagCategory.SKILL, key="tech_万剑诀", value="功法=万剑诀"),
        Tag(category=TagCategory.SKILL, key="tech_逍遥游", value="功法=逍遥游"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert scenarios.count("has_technique") == 1


def test_no_skill_tags_no_has_technique():
    ts = _make_tagset(
        Tag(category=TagCategory.IDENTITY, key="faction", value="门派=万剑山庄"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "has_technique" not in scenarios


# ══════════════════════════════════════════════════════════════════════════════
# determine_scenario_pool — relationships (bonds)
# ══════════════════════════════════════════════════════════════════════════════


def test_companion_bond_adds_has_companion():
    ts = _make_tagset(
        Tag(category=TagCategory.BOND, key="companion_wang", value="与王师兄交好"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "has_companion" in scenarios


def test_rival_bond_adds_has_rival():
    ts = _make_tagset(
        Tag(category=TagCategory.BOND, key="rival_zhang", value="与张师兄敌对"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "has_rival" in scenarios


def test_both_companion_and_rival():
    ts = _make_tagset(
        Tag(category=TagCategory.BOND, key="companion_wang", value="与王师兄交好"),
        Tag(category=TagCategory.BOND, key="rival_zhang", value="与张师兄敌对"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "has_companion" in scenarios
    assert "has_rival" in scenarios


# ══════════════════════════════════════════════════════════════════════════════
# determine_scenario_pool — states
# ══════════════════════════════════════════════════════════════════════════════


def test_injured_state_adds_injured():
    ts = _make_tagset(
        Tag(category=TagCategory.STATE, key="injured", value="伤势严重"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "injured" in scenarios


def test_blessed_state_adds_blessed():
    ts = _make_tagset(
        Tag(category=TagCategory.STATE, key="blessed_by_heaven", value="天赐祝福"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "blessed" in scenarios


def test_hunted_state_adds_hunted():
    ts = _make_tagset(
        Tag(category=TagCategory.STATE, key="hunted_by_demon", value="被魔修追杀"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "hunted" in scenarios


def test_multiple_states_add_all():
    ts = _make_tagset(
        Tag(category=TagCategory.STATE, key="injured_leg", value="腿伤"),
        Tag(category=TagCategory.STATE, key="blessed_by_god", value="神灵庇佑"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "injured" in scenarios
    assert "blessed" in scenarios


# ══════════════════════════════════════════════════════════════════════════════
# determine_scenario_pool — memories
# ══════════════════════════════════════════════════════════════════════════════


def test_childhood_memory_adds_childhood_special():
    ts = _make_tagset(
        Tag(category=TagCategory.BOND, key="childhood_memory_village", value="童年村庄记忆"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "childhood_special" in scenarios


def test_childhood_memory_with_other_bonds():
    ts = _make_tagset(
        Tag(category=TagCategory.BOND, key="childhood_memory", value="童年回忆"),
        Tag(category=TagCategory.BOND, key="companion_wang", value="与王师兄交好"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 20})
    assert "childhood_special" in scenarios
    assert "has_companion" in scenarios


# ══════════════════════════════════════════════════════════════════════════════
# determine_scenario_pool — combined scenarios
# ══════════════════════════════════════════════════════════════════════════════


def test_full_scenario_pool_with_faction_skills_bonds_states():
    ts = _make_tagset(
        Tag(category=TagCategory.IDENTITY, key="faction", value="门派=万剑山庄"),
        Tag(category=TagCategory.SKILL, key="tech_万剑诀", value="功法=万剑诀"),
        Tag(category=TagCategory.BOND, key="companion_wang", value="与王师兄交好"),
        Tag(category=TagCategory.STATE, key="injured", value="伤势严重"),
    )
    scenarios = determine_scenario_pool(ts, {"age": 30})
    assert "generic_daily" in scenarios
    assert "faction_万剑山庄" in scenarios
    assert "faction_life" in scenarios
    assert "faction_senior" in scenarios
    assert "has_technique" in scenarios
    assert "has_companion" in scenarios
    assert "injured" in scenarios


# ══════════════════════════════════════════════════════════════════════════════
# match_scenarios — filtering logic
# ══════════════════════════════════════════════════════════════════════════════


def test_match_scenarios_no_scenario_field_pass_through():
    templates = [
        {"id": "t1", "type": "daily"},
        {"id": "t2", "type": "adventure"},
    ]
    scenarios = ["generic_daily", "faction_万剑山庄"]
    result = match_scenarios(templates, scenarios)
    assert len(result) == 2


def test_match_scenarios_empty_scenario_list_pass_through():
    templates = [
        {"id": "t1", "scenarios": []},
        {"id": "t2", "scenarios": None},
    ]
    scenarios = ["faction_万剑山庄"]
    result = match_scenarios(templates, scenarios)
    assert len(result) == 2


def test_match_scenarios_intersection_match():
    templates = [
        {"id": "t1", "scenarios": ["faction_万剑山庄", "faction_life"]},
        {"id": "t2", "scenarios": ["faction_逍遥派", "freedom_path"]},
    ]
    scenarios = ["generic_daily", "faction_万剑山庄"]
    result = match_scenarios(templates, scenarios)
    assert len(result) == 1
    assert result[0]["id"] == "t1"


def test_match_scenarios_no_matching_scenarios_returns_empty():
    templates = [
        {"id": "t1", "scenarios": ["faction_逍遥派"]},
        {"id": "t2", "scenarios": ["sword_ritual"]},
    ]
    scenarios = ["generic_daily"]
    result = match_scenarios(templates, scenarios)
    assert result == []


def test_match_scenarios_mixed_templates():
    templates = [
        {"id": "t1", "type": "daily"},
        {"id": "t2", "scenarios": ["faction_万剑山庄", "faction_life"]},
        {"id": "t3", "scenarios": ["faction_逍遥派"]},
        {"id": "t4", "scenarios": []},
    ]
    scenarios = ["generic_daily", "faction_万剑山庄"]
    result = match_scenarios(templates, scenarios)
    matched_ids = {t["id"] for t in result}
    assert matched_ids == {"t1", "t2", "t4"}


def test_match_scenarios_empty_pool_returns_only_unscoped():
    templates = [
        {"id": "t1", "scenarios": ["faction_万剑山庄"]},
        {"id": "t2", "scenarios": []},
        {"id": "t3", "scenarios": ["faction_逍遥派"]},
    ]
    result = match_scenarios(templates, [])
    matched_ids = {t["id"] for t in result}
    assert matched_ids == {"t2"}
