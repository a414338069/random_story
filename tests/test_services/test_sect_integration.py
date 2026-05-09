"""Integration tests for sect joining system."""

import random
from unittest.mock import patch

import pytest

from app.models.tags import Tag, TagCategory, TagSet
from app.services.event_engine import load_templates, filter_templates
from app.services.game_service import (
    start_game,
    get_next_event,
    process_choice,
    get_state,
    _random_sect_for_player,
    _games,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_TALENT_IDS = ["f01", "l02", "x03"]


def _make_attrs(root_bone=3, comprehension=3, mindset=2, luck=2):
    return {"rootBone": root_bone, "comprehension": comprehension, "mindset": mindset, "luck": luck}


def _insert_current_event(session_id, options=None):
    if options is None:
        options = [
            {"id": "opt1", "text": "继续", "consequences": {"cultivation_gain": 10, "age_advance": True}},
        ]
    _games[session_id]["_current_event"] = {
        "id": "test_sect_event",
        "type": "bottleneck",
        "title": "门派选择",
        "options": options,
    }


def _advance_age(state, target_age):
    """Advance player age and lifespan to target for testing."""
    state["age"] = target_age
    state["lifespan"] = max(state["lifespan"], target_age + 10)
    state["cultivation"] = 0


# ---------------------------------------------------------------------------
# test_sect_invitation_has_decline_option
# ---------------------------------------------------------------------------


def test_sect_invitation_has_decline_option():
    """bottleneck_000 has 4 options, last one has no faction_assign and has tag_add."""
    templates = load_templates()
    template = next(t for t in templates if t["id"] == "bottleneck_000_sect_join")
    options = template.get("default_options", [])
    assert len(options) == 4, f"Expected 4 options, got {len(options)}"

    # Verify the 4th option (decline)
    decline_opt = options[3]
    assert decline_opt["id"] == "sect_rogue"
    assert "faction_assign" not in decline_opt.get("consequences", {})

    # Verify decline option adds the decided_rogue tag
    tag_add = decline_opt.get("consequences", {}).get("tag_add", [])
    assert "identity:decided_rogue" in tag_add

    # Verify first 3 options still have faction_assign
    for i in range(3):
        assert "faction_assign" in options[i].get("consequences", {})


def test_bottleneck_005_has_random_assign():
    """bottleneck_005 opt1 has faction_assign='随机分配' and opt2 has decline tag."""
    templates = load_templates()
    template = next(t for t in templates if t["id"] == "bottleneck_005")
    options = template.get("default_options", [])

    opt1 = options[0]
    assert opt1["consequences"]["faction_assign"] == "随机分配"

    opt2 = options[1]
    assert "identity:decided_rogue" in opt2.get("consequences", {}).get("tag_add", [])


# ---------------------------------------------------------------------------
# test_sect_join_validates_conditions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sect_join_validates_conditions():
    """When check_join_conditions returns False, faction falls back to '散修'."""
    random.seed(42)
    result = start_game("测试角色", "男", VALID_TALENT_IDS, _make_attrs(2, 2, 3, 3))
    session_id = result["session_id"]
    state = get_state(session_id)
    _advance_age(state, 10)

    faction_assign = "万剑山庄"
    options = [
        {
            "id": "opt1",
            "text": "加入万剑山庄",
            "consequences": {
                "faction_assign": faction_assign,
                "cultivation_gain": 20,
                "age_advance": True,
            },
        },
    ]
    _insert_current_event(session_id, options)

    with patch(
        "app.services.game_service.sect_service.check_join_conditions",
        return_value=False,
    ):
        process_choice(session_id, "opt1")

    state = get_state(session_id)
    assert state["faction"] == "散修", (
        f"Expected faction='散修' when conditions fail, got '{state['faction']}'"
    )


# ---------------------------------------------------------------------------
# test_sect_join_awards_techniques
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sect_join_awards_techniques():
    """When joining a sect, techniques are added to state."""
    random.seed(43)
    result = start_game("测试角色2", "男", VALID_TALENT_IDS, _make_attrs(4, 2, 2, 2))
    session_id = result["session_id"]
    state = get_state(session_id)
    _advance_age(state, 10)

    mock_techs = [{"name": "万剑诀", "grade": "灵品", "attribute": "金"}]

    options = [
        {
            "id": "opt1",
            "text": "加入万剑山庄",
            "consequences": {
                "faction_assign": "万剑山庄",
                "cultivation_gain": 20,
                "age_advance": True,
            },
        },
    ]
    _insert_current_event(session_id, options)

    with patch(
        "app.services.game_service.sect_service.check_join_conditions",
        return_value=True,
    ), patch(
        "app.services.game_service.sect_service.get_sect_techniques",
        return_value=mock_techs,
    ):
        process_choice(session_id, "opt1")

    state = get_state(session_id)
    assert state["faction"] == "万剑山庄"
    assert "万剑诀" in state.get("techniques", [])
    assert "灵品" in state.get("technique_grades", [])


# ---------------------------------------------------------------------------
# test_random_sect_for_player
# ---------------------------------------------------------------------------


def test_random_sect_for_player_eligible():
    """Player with high attributes gets a random eligible sect (not '散修')."""
    attrs = _make_attrs(root_bone=5, comprehension=5, mindset=3, luck=2)
    random.seed(123)
    result = _random_sect_for_player(attrs)
    assert result in ("万剑山庄", "逍遥派", "金刚寺"), f"Got unexpected sect: {result}"


def test_random_sect_for_player_none_eligible():
    """Player with low attributes falls back to '散修'."""
    attrs = _make_attrs(root_bone=2, comprehension=2, mindset=2, luck=4)
    random.seed(123)
    result = _random_sect_for_player(attrs)
    assert result == "散修", f"Expected '散修', got '{result}'"


# ---------------------------------------------------------------------------
# test_decided_rogue_filters_sect_templates
# ---------------------------------------------------------------------------


def test_decided_rogue_filters_requires_any_faction():
    """Templates with requires_any_faction: true are skipped when player has decided_rogue tag."""
    rogue_tag = Tag(category=TagCategory.IDENTITY, key="decided_rogue", value="散修之路")
    tags = TagSet()
    tags.add(rogue_tag)

    player_state = {
        "realm": "炼气",
        "age": 20,
        "faction": "",
        "tags": tags,
    }

    # Build a controlled template list including one with requires_any_faction
    templates = [
        {
            "id": "daily_001",
            "type": "daily",
            "trigger_conditions": {},
            "trigger_tags": {"require_all": [], "require_any": [], "block": []},
        },
        {
            "id": "sect_001",
            "type": "sect",
            "trigger_conditions": {"requires_any_faction": True},
            "trigger_tags": {"require_all": [], "require_any": [], "block": []},
        },
    ]
    filtered = filter_templates(templates, player_state)
    filtered_ids = [t["id"] for t in filtered]
    assert "sect_001" not in filtered_ids, (
        "Templates with requires_any_faction should be filtered for rogue players"
    )
    assert "daily_001" in filtered_ids, "Non-faction templates should still pass"


def test_decided_rogue_still_passes_regular_templates():
    """Player with decided_rogue still sees non-faction templates."""
    rogue_tag = Tag(category=TagCategory.IDENTITY, key="decided_rogue", value="散修之路")
    tags = TagSet()
    tags.add(rogue_tag)

    player_state = {
        "realm": "凡人",
        "age": 15,
        "faction": "",
        "tags": tags,
    }

    templates = load_templates()
    filtered = filter_templates(templates, player_state)
    assert len(filtered) > 0, "Rogue players should still see some templates"
    # No template in the result should require_any_faction
    for t in filtered:
        cond = t.get("trigger_conditions", {})
        assert not cond.get("requires_any_faction", False), (
            f"Template {t['id']} should have been filtered for rogue"
        )
