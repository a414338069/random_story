"""Tests for scoring service (Task 10).

RED phase: All tests should fail initially.
"""

import pytest

from app.models.player import PlayerState
from app.services.scoring import (
    determine_ending,
    calculate_score,
    get_grade,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_player(
    realm: str = "凡人",
    lifespan: int = 80,
    techniques: list[str] | None = None,
) -> PlayerState:
    """Create a minimal valid PlayerState for testing."""
    return PlayerState(
        id="test-id",
        name="TestPlayer",
        root_bone=3,
        comprehension=3,
        mindset=2,
        luck=2,
        realm=realm,
        lifespan=lifespan,
        techniques=techniques or [],
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )


# ---------------------------------------------------------------------------
# determine_ending()
# ---------------------------------------------------------------------------


class TestDetermineEnding:
    """MVP ending determination — 3 endings triggered, 5 defined but dormant."""

    def test_ascended_feisheng(self):
        """大乘 + ascended=True → "飞升成仙"."""
        player = _make_player(realm="大乘", lifespan=20000)
        ending = determine_ending(player, age=500, ascended=True)
        assert ending == "飞升成仙"

    def test_heti_gongde_yuanman(self):
        """合体 + age >= lifespan → "功德圆满" (realm order 7 >= 6 合体)."""
        player = _make_player(realm="合体", lifespan=8000)
        ending = determine_ending(player, age=8000)
        assert ending == "功德圆满"

    def test_dacheng_age_over_lifespan_gongde(self):
        """大乘 + age >= lifespan → "功德圆满" (realm order 8 >= 6)."""
        player = _make_player(realm="大乘", lifespan=20000)
        ending = determine_ending(player, age=20000)
        assert ending == "功德圆满"

    def test_mortal_shouzhong_zhengguo(self):
        """凡人 + age >= lifespan → "寿终正寝" (realm < 合体)."""
        player = _make_player(realm="凡人", lifespan=80)
        ending = determine_ending(player, age=80)
        assert ending == "寿终正寝"

    def test_lianqi_shouzhong(self):
        """练气 + age >= lifespan → "寿终正寝" (realm order 2 < 6)."""
        player = _make_player(realm="练气", lifespan=120)
        ending = determine_ending(player, age=120)
        assert ending == "寿终正寝"

    def test_default_shouzhong(self):
        """No special condition → default "寿终正寝"."""
        player = _make_player(realm="凡人", lifespan=80)
        ending = determine_ending(player, age=30)
        assert ending == "寿终正寝"

    def test_ascended_any_realm(self):
        """ascended=True at low realm still → "飞升成仙"."""
        player = _make_player(realm="金丹", lifespan=500)
        ending = determine_ending(player, age=200, ascended=True)
        assert ending == "飞升成仙"

    def test_ascended_dujie_feisheng(self):
        """渡劫飞升 + ascended=True → "飞升成仙"."""
        player = _make_player(realm="渡劫飞升", lifespan=999999)
        ending = determine_ending(player, age=999999, ascended=True)
        assert ending == "飞升成仙"

    def test_lifespan_infinite_not_shouzhong(self):
        """渡劫飞升(lifespan='无限') not ascended → 不寿终, default to 寿终正寝."""
        player = _make_player(realm="渡劫飞升", lifespan=999999)
        ending = determine_ending(player, age=999999, ascended=False)
        assert ending == "寿终正寝"


# ---------------------------------------------------------------------------
# calculate_score() — determinism & boundary
# ---------------------------------------------------------------------------


class TestCalculateScore:
    """Score calculation — 4 dimensions, deterministic, 0-100 range."""

    def test_deterministic(self):
        """同一状态调用两次 → 分数完全相同."""
        player = _make_player(realm="练气", lifespan=120)
        ending = "寿终正寝"
        s1 = calculate_score(player, ending, age=120, technique_grades=[])
        s2 = calculate_score(player, ending, age=120, technique_grades=[])
        assert s1 == s2

    def test_score_range_low(self):
        """凡人 + 无功法 + 寿终 + 青壮年 → score < 20."""
        player = _make_player(realm="凡人", lifespan=80)
        score = calculate_score(player, "寿终正寝", age=30, technique_grades=[])
        assert score < 20

    def test_score_range_high(self):
        """渡劫飞升 + 飞升成仙 + 仙品功法 → score >= 95."""
        player = _make_player(realm="渡劫飞升", lifespan=20000)
        score = calculate_score(
            player, "飞升成仙", age=20000, technique_grades=["仙品"]
        )
        assert score >= 95

    def test_score_max_100(self):
        """Maximum possible score should be 100."""
        player = _make_player(realm="渡劫飞升", lifespan=20000)
        score = calculate_score(
            player, "飞升成仙", age=20000, technique_grades=["仙品"]
        )
        assert score <= 100

    def test_score_min_0(self):
        """Minimum possible score should be 0."""
        player = _make_player(realm="凡人", lifespan=80)
        score = calculate_score(player, "寿终正寝", age=0, technique_grades=[])
        assert score >= 0

    def test_realm_score_component(self):
        """境界分: 筑基(order=3 → 0-indexed=2) should give (2/8)*50 = 12.5 contribution."""
        player = _make_player(realm="筑基", lifespan=200)
        # age=0 → lifespan_score=0, no techniques → 0, ending=寿终正寝→5
        # Total = 12.5 + 0 + 0 + 5 = 17.5 → 18
        score = calculate_score(player, "寿终正寝", age=0, technique_grades=[])
        assert score == 18

    def test_lifespan_score_component(self):
        """寿命分: half lifespan lived → 10 points."""
        player = _make_player(realm="凡人", lifespan=80)
        # age=40 → min(40/80, 1)*20 = 10
        # realm=0, tech=0, ending=5 → total=15
        score = calculate_score(player, "寿终正寝", age=40, technique_grades=[])
        assert score == 15

    def test_lifespan_score_max(self):
        """寿命分 capped: age >= lifespan → 20 points."""
        player = _make_player(realm="凡人", lifespan=80)
        score_over = calculate_score(player, "寿终正寝", age=100, technique_grades=[])
        score_at = calculate_score(player, "寿终正寝", age=80, technique_grades=[])
        assert score_over == score_at  # both capped at 20 lifespan points

    def test_technique_lingpin_score(self):
        """功法分: 灵品(0.5) technique adds 10 points vs no technique."""
        player = _make_player(realm="凡人", lifespan=80)
        s_none = calculate_score(player, "寿终正寝", age=0, technique_grades=[])
        s_ling = calculate_score(player, "寿终正寝", age=0, technique_grades=["灵品"])
        # diff should be exactly 0.5 * 20 = 10
        assert s_ling - s_none == 10

    def test_multiple_techniques_average(self):
        """多功法取平均: 凡品(0.25) + 仙品(1.0) = avg 0.625 → score 12.5."""
        player = _make_player(realm="凡人", lifespan=80)
        score = calculate_score(
            player, "寿终正寝", age=0, technique_grades=["凡品", "仙品"]
        )
        # 0 (realm) + 0 (lifespan) + (0.625 * 20=12.5) + 5 (ending) = 17.5 → 18
        assert score == 18

    def test_technique_all_grades(self):
        """All four grade values map to correct scores."""
        player = _make_player(realm="凡人", lifespan=80)
        base = calculate_score(player, "寿终正寝", age=0, technique_grades=[])
        # Each grade adds (grade_value * 20) to raw total
        for grades, expected_add in [
            (["凡品"], 5),   # 0.25 * 20
            (["灵品"], 10),  # 0.5 * 20
            (["玄品"], 15),  # 0.75 * 20
            (["仙品"], 20),  # 1.0 * 20
        ]:
            s = calculate_score(player, "寿终正寝", age=0, technique_grades=grades)
            # base is 5 (寿终正寝 ending component with no other contributions)
            assert s - base == expected_add, f"Grade {grades} expected +{expected_add}"

    def test_empty_techniques_zero_score(self):
        """空功法列表 → 功法分为 0."""
        player = _make_player(realm="凡人", lifespan=80)
        s_empty = calculate_score(player, "寿终正寝", age=0, technique_grades=[])
        s_none = calculate_score(player, "寿终正寝", age=0, technique_grades=[])
        assert s_empty == s_none

    def test_ending_bonus_feisheng(self):
        """飞升成仙 ending bonus = 1.0 → 10 points."""
        player = _make_player(realm="凡人", lifespan=80)
        s = calculate_score(player, "飞升成仙", age=0, technique_grades=[])
        # 0 + 0 + 0 + 10 = 10
        assert s == 10

    def test_ending_bonus_gongde(self):
        """功德圆满 ending bonus = 0.8 → 8 points."""
        player = _make_player(realm="凡人", lifespan=80)
        s = calculate_score(player, "功德圆满", age=0, technique_grades=[])
        assert s == 8

    def test_ending_bonus_shouzhong(self):
        """寿终正寝 ending bonus = 0.5 → 5 points."""
        player = _make_player(realm="凡人", lifespan=80)
        s = calculate_score(player, "寿终正寝", age=0, technique_grades=[])
        assert s == 5

    def test_ending_bonus_unknown_default(self):
        """其他结局 ending bonus = 0.3 (default) → 3 points."""
        player = _make_player(realm="凡人", lifespan=80)
        for ending in ["魔道至尊", "战死沙场", "走火入魔", "意外身亡", "道心破碎"]:
            s = calculate_score(player, ending, age=0, technique_grades=[])
            assert s == 3, f"Ending '{ending}' should give default 3 points"

    def test_lifespan_infinite_score_full(self):
        """渡劫飞升(lifespan='无限') → 寿命分满分20, realm分满分50."""
        player = _make_player(realm="渡劫飞升", lifespan=999999)
        score = calculate_score(player, "寿终正寝", age=500, technique_grades=[])
        # realm: 8/8*50=50, lifespan: 20, tech: 0, ending: 5 = 75
        assert score == 75


# ---------------------------------------------------------------------------
# get_grade()
# ---------------------------------------------------------------------------


class TestGetGrade:
    """Score → Grade mapping (7 tiers)."""

    @pytest.mark.parametrize("score,expected", [
        (100, "SSS"),
        (97, "SSS"),
        (95, "SSS"),
        (94, "SS"),
        (90, "SS"),
        (85, "SS"),
        (84, "S"),
        (80, "S"),
        (75, "S"),
        (74, "A"),
        (65, "A"),
        (60, "A"),
        (59, "B"),
        (50, "B"),
        (40, "B"),
        (39, "C"),
        (30, "C"),
        (20, "C"),
        (19, "D"),
        (10, "D"),
        (0, "D"),
    ])
    def test_grade_mapping(self, score: int, expected: str):
        assert get_grade(score) == expected

    def test_negative_clamps_to_d(self):
        """Below 0 still returns D (safety)."""
        assert get_grade(-5) == "D"

    def test_above_100_returns_sss(self):
        """Above 100 still returns SSS (safety)."""
        assert get_grade(999) == "SSS"
