"""Tests for talent effect utility functions (T2)."""

import pytest

from app.services.talent_service import (
    get_active_modifiers,
    has_talent_effect,
    _apply_talent_attr_bonuses,
    load_talents,
)


# ---------------------------------------------------------------------------
# get_active_modifiers()
# ---------------------------------------------------------------------------


def test_get_active_modifiers_aggregates_correctly():
    """Multiple talents' modifiers should sum correctly (additive)."""
    # f01: max_health_bonus=20
    # l01: max_health_bonus=50, physical_damage_bonus=0.15
    result = get_active_modifiers(["f01", "l01"])
    assert result["max_health_bonus"] == pytest.approx(70.0)
    assert result["physical_damage_bonus"] == pytest.approx(0.15)


def test_get_active_modifiers_empty_list():
    """Empty talent list should return empty dict."""
    result = get_active_modifiers([])
    assert result == {}


def test_get_active_modifiers_missing_effects(monkeypatch):
    """Talent without effects field should be handled safely (no crash)."""
    # Monkeypatch load_talents to return a talent missing 'effects'
    original = load_talents()
    modified = [{"id": "bad_talent", "name": "Bad", "grade": "凡品"}] + original
    monkeypatch.setattr(
        "app.services.talent_service.load_talents", lambda: modified
    )
    # Should not raise KeyError — returns empty dict for talent with no effects
    result = get_active_modifiers(["bad_talent"])
    assert result == {}


# ---------------------------------------------------------------------------
# has_talent_effect()
# ---------------------------------------------------------------------------


def test_has_talent_effect_positive():
    """Should return True when a talent has the effect in positive_effects."""
    # l06 has positive_effects.modifiers.breakthrough_pill_chance=0.25
    assert has_talent_effect(["l06"], "breakthrough_pill_chance") is True


def test_has_talent_effect_negative():
    """Should return False when no talent has the effect key."""
    assert has_talent_effect(["f01", "x01"], "nonexistent_effect_key") is False


# ---------------------------------------------------------------------------
# _apply_talent_attr_bonuses()
# ---------------------------------------------------------------------------


def test_apply_talent_attr_bonuses_correct_sum():
    """Multi-talent attr_bonuses sum and clamp to [0, 10]."""
    base = {"root_bone": 8, "comprehension": 0, "mindset": 0, "luck": 0}
    # f01: root_bone +1
    # x01: root_bone +5, comprehension +5
    # total: root_bone = 8+1+5=14→10, comprehension = 0+0+5=5
    result = _apply_talent_attr_bonuses(["f01", "x01"], base)
    assert result["root_bone"] == 10
    assert result["comprehension"] == 5
    assert result["mindset"] == 0
    assert result["luck"] == 0


def test_apply_talent_attr_bonuses_no_talent():
    """Empty talent list should return original attributes unchanged."""
    base = {"root_bone": 5, "comprehension": 3, "mindset": 1, "luck": 1}
    result = _apply_talent_attr_bonuses([], base)
    assert result == base
