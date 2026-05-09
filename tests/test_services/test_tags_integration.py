"""Tests for tag interaction with breakthrough and scoring systems (Task 16)."""

import random

import pytest

from app.models.tags import Tag, TagCategory, TagSet
from app.models.player import PlayerState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tags() -> TagSet:
    """Create a fresh empty TagSet."""
    return TagSet(tags=[])


def _make_tag(
    category: TagCategory,
    key: str,
    value: str,
    is_active: bool = True,
    years_active: int = -1,
    priority: int = 0,
) -> Tag:
    return Tag(
        category=category,
        key=key,
        value=value,
        description=f"Test {key}",
        is_active=is_active,
        years_active=years_active,
        priority=priority,
    )


def _make_player(
    realm: str = "凡人",
    lifespan: int = 80,
) -> PlayerState:
    """Create a minimal valid PlayerState for scoring tests."""
    return PlayerState(
        id="test-id",
        name="TestPlayer",
        root_bone=3,
        comprehension=3,
        mindset=2,
        luck=2,
        realm=realm,
        lifespan=lifespan,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )


# ============================================================================
# Breakthrough — tag-based modifiers
# ============================================================================


class TestBreakthroughTagModifiers:
    """Tag effects on breakthrough success rate."""

    def test_master_bond_increases_rate(self):
        """bond_master → +5% success rate."""
        from app.services.breakthrough import calculate_success_rate

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.BOND, "bond_master", "与大师兄交好"))

        player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
        base_rate = calculate_success_rate(player)
        tag_rate = calculate_success_rate(player, tags=tags)
        assert tag_rate == pytest.approx(base_rate + 0.05)

    def test_blessed_state_increases_rate(self):
        """state_blessed (active) → +3% success rate."""
        from app.services.breakthrough import calculate_success_rate

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.STATE, "state_blessed", "祝福状态", is_active=True))

        player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
        base_rate = calculate_success_rate(player)
        tag_rate = calculate_success_rate(player, tags=tags)
        assert tag_rate == pytest.approx(base_rate + 0.03)

    def test_blessed_inactive_no_effect(self):
        """Inactive state_blessed → no modifier."""
        from app.services.breakthrough import calculate_success_rate

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.STATE, "state_blessed", "祝福状态", is_active=False))

        player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
        base_rate = calculate_success_rate(player)
        tag_rate = calculate_success_rate(player, tags=tags)
        assert tag_rate == base_rate

    def test_injured_state_decreases_rate(self):
        """state_injured (active) → -10% success rate."""
        from app.services.breakthrough import calculate_success_rate

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.STATE, "state_injured", "受伤状态", is_active=True, years_active=3))

        player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
        base_rate = calculate_success_rate(player)
        tag_rate = calculate_success_rate(player, tags=tags)
        assert tag_rate == pytest.approx(base_rate - 0.10)

    def test_injured_inactive_no_effect(self):
        """Inactive state_injured → no modifier."""
        from app.services.breakthrough import calculate_success_rate

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.STATE, "state_injured", "受伤状态", is_active=False))

        player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
        base_rate = calculate_success_rate(player)
        tag_rate = calculate_success_rate(player, tags=tags)
        assert tag_rate == base_rate

    def test_combined_tag_modifiers(self):
        """Master +5% + Blessed +3% + Injured -10% = net -2% (additive)."""
        from app.services.breakthrough import calculate_success_rate

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.BOND, "bond_master", "与大师兄交好"))
        tags.add(_make_tag(TagCategory.STATE, "state_blessed", "祝福状态", is_active=True))
        tags.add(_make_tag(TagCategory.STATE, "state_injured", "受伤状态", is_active=True, years_active=2))

        player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
        base_rate = calculate_success_rate(player)
        tag_rate = calculate_success_rate(player, tags=tags)
        assert tag_rate == pytest.approx(base_rate + 0.05 + 0.03 - 0.10)

    def test_tag_modifiers_with_pill(self):
        """Tag modifiers stack with pill bonus."""
        from app.services.breakthrough import calculate_success_rate

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.BOND, "bond_master", "与大师兄交好"))

        player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
        rate = calculate_success_rate(player, use_pill=True, tags=tags)
        assert rate == pytest.approx(0.70)

    def test_tag_modifiers_respect_rate_bounds(self):
        """Tag modifiers still respect [0.05, 0.95] bounds."""
        from app.services.breakthrough import calculate_success_rate

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.STATE, "state_injured", "受伤状态", is_active=True))

        player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "大乘"}
        rate = calculate_success_rate(player, tags=tags)
        # 0.50 - 0.35 - 0.10 = 0.05 → at lower bound
        assert rate >= 0.05

    def test_no_tags_no_effect(self):
        """tags=None → rate unchanged."""
        from app.services.breakthrough import calculate_success_rate

        player = {"rootBone": 0, "comprehension": 0, "mindset": 0, "realm": "凡人"}
        rate = calculate_success_rate(player, tags=None)
        assert rate == 0.50

    def test_attempt_breakthrough_defaults_tags_to_none(self):
        """attempt_breakthrough() without tags still works (backward compatible)."""
        from app.services.breakthrough import attempt_breakthrough

        player = {
            "rootBone": 10, "comprehension": 10, "mindset": 10,
            "realm": "凡人", "cultivation": 50, "talent_ids": [],
        }
        random.seed(1)
        result = attempt_breakthrough(player)
        assert result.success is True
        assert result.new_realm == "炼气"


class TestBreakthroughRealmTagUpdate:
    """Breakthrough success updates realm_current tag."""

    def test_success_updates_realm_tag(self):
        """Successful breakthrough → realm_current tag added."""
        from app.services.breakthrough import attempt_breakthrough

        tags = _make_tags()
        player = {
            "rootBone": 10, "comprehension": 10, "mindset": 10,
            "realm": "凡人", "cultivation": 50, "talent_ids": [],
        }
        random.seed(1)
        result = attempt_breakthrough(player, tags=tags)
        assert result.success is True

        realm_tag = tags.get_by_key("realm_current")
        assert realm_tag is not None
        assert realm_tag.category == TagCategory.STATE
        assert "境界=炼气" == realm_tag.value

    def test_success_from_lianqi_to_zhuji_tag(self):
        """Breakthrough from 炼气 → 筑基 updates realm tag."""
        from app.services.breakthrough import attempt_breakthrough

        tags = _make_tags()
        # 炼气 realm penalty = 0.05, so rate = 0.50 + 0.50 + 0.30 + 0.20 - 0.05 = 1.45 → cap 0.95
        # seed 1: random < 0.95 → success
        player = {
            "rootBone": 10, "comprehension": 10, "mindset": 10,
            "realm": "炼气", "cultivation": 200, "talent_ids": [],
        }
        random.seed(1)
        result = attempt_breakthrough(player, tags=tags)
        assert result.success is True

        realm_tag = tags.get_by_key("realm_current")
        assert realm_tag is not None
        assert realm_tag.value == "境界=筑基"

    def test_failure_does_not_update_tag(self):
        """Failed breakthrough → realm_current tag NOT added."""
        from app.services.breakthrough import attempt_breakthrough

        tags = _make_tags()
        player = {
            "rootBone": 0, "comprehension": 0, "mindset": 0,
            "realm": "凡人", "cultivation": 100, "talent_ids": [],
        }
        random.seed(2)
        result = attempt_breakthrough(player, tags=tags)
        assert result.success is False

        realm_tag = tags.get_by_key("realm_current")
        assert realm_tag is None

    def test_no_tags_breakthrough_still_works(self):
        """tags=None → no crash, no tag side effect."""
        from app.services.breakthrough import attempt_breakthrough

        player = {
            "rootBone": 10, "comprehension": 10, "mindset": 10,
            "realm": "凡人", "cultivation": 50, "talent_ids": [],
        }
        random.seed(1)
        result = attempt_breakthrough(player, tags=None)
        assert result.success is True


# ============================================================================
# Scoring — tag-based modifiers
# ============================================================================


class TestCalculateTagScore:
    """_calculate_tag_score() unit tests."""

    def test_empty_tags_returns_zero(self):
        from app.services.scoring import _calculate_tag_score

        assert _calculate_tag_score(None) == 0.0
        assert _calculate_tag_score(_make_tags()) == 0.0

    def test_single_category_one_point(self):
        from app.services.scoring import _calculate_tag_score

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.IDENTITY, "identity_1", "散修"))
        assert _calculate_tag_score(tags) == pytest.approx(2.0)

    def test_two_categories_four_points(self):
        from app.services.scoring import _calculate_tag_score

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.IDENTITY, "identity_1", "散修"))
        tags.add(_make_tag(TagCategory.STATE, "state_1", "正常"))
        assert _calculate_tag_score(tags) == pytest.approx(4.0)

    def test_all_four_categories_eight_points(self):
        from app.services.scoring import _calculate_tag_score

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.IDENTITY, "identity_1", "散修"))
        tags.add(_make_tag(TagCategory.SKILL, "skill_1", "剑法"))
        tags.add(_make_tag(TagCategory.BOND, "bond_1", "羁绊"))
        tags.add(_make_tag(TagCategory.STATE, "state_1", "状态"))
        assert _calculate_tag_score(tags) == pytest.approx(8.0)

    def test_variety_capped_at_eight(self):
        """Even with many tags, variety bonus caps at 8.0 (4 categories × 2)."""
        from app.services.scoring import _calculate_tag_score

        tags = _make_tags()
        # 4 categories, multiple tags each
        tags.add(_make_tag(TagCategory.IDENTITY, "identity_1", "散修"))
        tags.add(_make_tag(TagCategory.IDENTITY, "identity_2", "剑修"))
        tags.add(_make_tag(TagCategory.SKILL, "skill_1", "剑法"))
        tags.add(_make_tag(TagCategory.SKILL, "skill_2", "遁法"))
        tags.add(_make_tag(TagCategory.BOND, "bond_1", "羁绊1"))
        tags.add(_make_tag(TagCategory.BOND, "bond_2", "羁绊2"))
        tags.add(_make_tag(TagCategory.STATE, "state_1", "状态1"))
        tags.add(_make_tag(TagCategory.STATE, "state_2", "状态2"))

        variety = _calculate_tag_score(tags)
        assert variety == pytest.approx(8.0)

    def test_inactive_tags_not_counted(self):
        """Only active tags count toward variety."""
        from app.services.scoring import _calculate_tag_score

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.IDENTITY, "identity_1", "散修", is_active=True))
        tags.add(_make_tag(TagCategory.SKILL, "skill_1", "剑法", is_active=False))
        tags.add(_make_tag(TagCategory.BOND, "bond_1", "羁绊", is_active=False))
        # Only 1 category active → 2.0
        assert _calculate_tag_score(tags) == pytest.approx(2.0)

    def test_master_lost_bond_adds_five(self):
        from app.services.scoring import _calculate_tag_score

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.BOND, "bond_master_lost", "与大师兄决裂"))
        # 1 category (BOND) = 2 points + 5 master_lost = 7
        assert _calculate_tag_score(tags) == pytest.approx(7.0)

    def test_master_lost_with_variety(self):
        from app.services.scoring import _calculate_tag_score

        tags = _make_tags()
        tags.add(_make_tag(TagCategory.IDENTITY, "identity_1", "散修"))
        tags.add(_make_tag(TagCategory.SKILL, "skill_1", "剑法"))
        tags.add(_make_tag(TagCategory.BOND, "bond_master_lost", "大师兄决裂"))
        # 3 categories × 2 = 6 + 5 = 11
        assert _calculate_tag_score(tags) == pytest.approx(11.0)


class TestScoringTagIntegration:
    """Tag integration with calculate_score() and determine_ending()."""

    def test_score_includes_tag_component(self):
        """Score with tags is higher than without."""
        from app.services.scoring import calculate_score

        player = _make_player(realm="筑基", lifespan=200)
        tags = _make_tags()
        tags.add(_make_tag(TagCategory.IDENTITY, "identity_1", "青云门弟子"))
        tags.add(_make_tag(TagCategory.SKILL, "skill_1", "剑法入门"))
        tags.add(_make_tag(TagCategory.BOND, "bond_master", "与大师兄交好"))
        tags.add(_make_tag(TagCategory.STATE, "state_1", "正常"))

        score_with = calculate_score(player, "寿终正寝", age=100, technique_grades=[], tags=tags)
        score_without = calculate_score(player, "寿终正寝", age=100, technique_grades=[], tags=None)
        assert score_with > score_without

    def test_master_lost_ending_daoxin_posui(self):
        """bond_master_lost → "道心破碎" ending (overrides normal ending)."""
        from app.services.scoring import determine_ending

        player = _make_player(realm="合体", lifespan=8000)
        tags = _make_tags()
        tags.add(_make_tag(TagCategory.BOND, "bond_master_lost", "与大师兄决裂"))

        ending = determine_ending(player, age=8000, tags=tags)
        assert ending == "道心破碎"

    def test_master_lost_overrides_gongde(self):
        """bond_master_lost takes priority over 功德圆满."""
        from app.services.scoring import determine_ending

        player = _make_player(realm="大乘", lifespan=20000)
        tags = _make_tags()
        tags.add(_make_tag(TagCategory.BOND, "bond_master_lost", "与大师兄决裂"))

        ending = determine_ending(player, age=20000, tags=tags)
        assert ending == "道心破碎"

    def test_master_lost_vs_ascended(self):
        """ascended=True takes priority over master_lost."""
        from app.services.scoring import determine_ending

        player = _make_player(realm="大乘", lifespan=20000)
        tags = _make_tags()
        tags.add(_make_tag(TagCategory.BOND, "bond_master_lost", "与大师兄决裂"))

        ending = determine_ending(player, age=500, ascended=True, tags=tags)
        assert ending == "飞升成仙"

    def test_no_tags_ending_unchanged(self):
        """tags=None → determine_ending unchanged from MVP behavior."""
        from app.services.scoring import determine_ending

        player = _make_player(realm="合体", lifespan=8000)
        ending = determine_ending(player, age=8000, tags=None)
        assert ending == "功德圆满"

    def test_no_tags_score_unchanged(self):
        """tags=None → calculate_score unchanged from MVP behavior."""
        from app.services.scoring import calculate_score

        player = _make_player(realm="筑基", lifespan=200)
        score = calculate_score(player, "寿终正寝", age=0, technique_grades=[], tags=None)
        # realm: 2/8*50=12.5, lifespan: 0, tech: 0, ending: 5, tag: 0 → 18
        assert score == 18

    def test_ending_daoxin_posui_default_bonus(self):
        """"道心破碎" is not in _ENDING_BONUS → uses default 0.3 bonus."""
        from app.services.scoring import calculate_score

        player = _make_player(realm="凡人", lifespan=80)
        score = calculate_score(player, "道心破碎", age=0, technique_grades=[])
        # 0 + 0 + 0 + 3 + 0 = 3
        assert score == 3
