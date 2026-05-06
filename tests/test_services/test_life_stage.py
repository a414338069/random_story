"""Tests for life stage system (Task T1 - structural-fix Wave 1).

TDD RED phase: These tests must fail initially before life_stage.py is created.
"""

import pytest

from app.services.life_stage import (
    LifeStage,
    get_life_stage,
    get_cultivation_multiplier,
    can_attempt_breakthrough,
    get_breakthrough_penalty,
)


# ---------------------------------------------------------------------------
# LifeStage enum boundary tests
# ---------------------------------------------------------------------------


class TestLifeStageEnum:
    def test_age_1_is_infant(self):
        """Age 1 (0-3) → INFANT."""
        assert get_life_stage(1) == LifeStage.INFANT

    def test_age_0_is_infant(self):
        """Age 0 (boundary) → INFANT."""
        assert get_life_stage(0) == LifeStage.INFANT

    def test_age_3_is_infant(self):
        """Age 3 (upper boundary of INFANT) → INFANT."""
        assert get_life_stage(3) == LifeStage.INFANT

    def test_age_4_is_child(self):
        """Age 4 (lower boundary of CHILD) → CHILD."""
        assert get_life_stage(4) == LifeStage.CHILD

    def test_age_5_is_child(self):
        """Age 5 (middle of CHILD) → CHILD."""
        assert get_life_stage(5) == LifeStage.CHILD

    def test_age_11_is_child(self):
        """Age 11 (upper boundary of CHILD) → CHILD."""
        assert get_life_stage(11) == LifeStage.CHILD

    def test_age_12_is_youth(self):
        """Age 12 (lower boundary of YOUTH) → YOUTH."""
        assert get_life_stage(12) == LifeStage.YOUTH

    def test_age_14_is_youth(self):
        """Age 14 (middle of YOUTH) → YOUTH."""
        assert get_life_stage(14) == LifeStage.YOUTH

    def test_age_15_is_youth(self):
        """Age 15 (upper boundary of YOUTH) → YOUTH."""
        assert get_life_stage(15) == LifeStage.YOUTH

    def test_age_16_is_cultivator(self):
        """Age 16 (lower boundary of CULTIVATOR) → CULTIVATOR."""
        assert get_life_stage(16) == LifeStage.CULTIVATOR

    def test_age_20_is_cultivator(self):
        """Age 20 (middle of CULTIVATOR) → CULTIVATOR."""
        assert get_life_stage(20) == LifeStage.CULTIVATOR

    def test_age_100_is_cultivator(self):
        """Age 100 (far above 16) → CULTIVATOR."""
        assert get_life_stage(100) == LifeStage.CULTIVATOR

    def test_enum_values_are_strings(self):
        """LifeStage values should be lowercase strings for JSON serialization."""
        assert isinstance(LifeStage.INFANT.value, str)
        assert LifeStage.INFANT.value == "infant"
        assert LifeStage.CHILD.value == "child"
        assert LifeStage.YOUTH.value == "youth"
        assert LifeStage.CULTIVATOR.value == "cultivator"


# ---------------------------------------------------------------------------
# get_cultivation_multiplier tests
# ---------------------------------------------------------------------------


class TestCultivationMultiplier:
    def test_multiplier_zero_for_infant(self):
        """INFANT (0-3) → multiplier = 0.0 (cannot cultivate)."""
        assert get_cultivation_multiplier(0) == 0.0
        assert get_cultivation_multiplier(3) == 0.0

    def test_multiplier_zero_for_child(self):
        """CHILD (4-11) → multiplier = 0.0 (cannot cultivate)."""
        assert get_cultivation_multiplier(4) == 0.0
        assert get_cultivation_multiplier(8) == 0.0
        assert get_cultivation_multiplier(11) == 0.0

    def test_multiplier_half_for_youth(self):
        """YOUTH (12-15) → multiplier = 0.5."""
        assert get_cultivation_multiplier(12) == 0.5
        assert get_cultivation_multiplier(14) == 0.5
        assert get_cultivation_multiplier(15) == 0.5

    def test_multiplier_full_for_cultivator(self):
        """CULTIVATOR (16+) → multiplier = 1.0."""
        assert get_cultivation_multiplier(16) == 1.0
        assert get_cultivation_multiplier(20) == 1.0
        assert get_cultivation_multiplier(100) == 1.0


# ---------------------------------------------------------------------------
# can_attempt_breakthrough tests
# ---------------------------------------------------------------------------


class TestCanAttemptBreakthrough:
    def test_breakthrough_blocked_for_youth(self):
        """Age < 16 → cannot attempt breakthrough."""
        assert can_attempt_breakthrough(10) is False
        assert can_attempt_breakthrough(15) is False
        assert can_attempt_breakthrough(0) is False
        assert can_attempt_breakthrough(12) is False

    def test_breakthrough_allowed_for_cultivator(self):
        """Age >= 16 → can attempt breakthrough."""
        assert can_attempt_breakthrough(16) is True
        assert can_attempt_breakthrough(25) is True
        assert can_attempt_breakthrough(100) is True


# ---------------------------------------------------------------------------
# get_breakthrough_penalty tests
# ---------------------------------------------------------------------------


class TestBreakthroughPenalty:
    def test_penalty_for_underage(self):
        """Age < 16 → breakthrough penalty = 0.5 (severe)."""
        assert get_breakthrough_penalty(10) == 0.5
        assert get_breakthrough_penalty(0) == 0.5
        assert get_breakthrough_penalty(15) == 0.5

    def test_no_penalty_for_adult(self):
        """Age >= 16 → no penalty."""
        assert get_breakthrough_penalty(16) == 0.0
        assert get_breakthrough_penalty(25) == 0.0
        assert get_breakthrough_penalty(100) == 0.0
