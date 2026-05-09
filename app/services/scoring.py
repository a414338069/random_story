"""Scoring service — ending determination, score calculation, and grade mapping.
 
All functions are pure and deterministic (same inputs always produce same output).
No AI involvement, no randomness.
"""

from __future__ import annotations

from app.models.player import PlayerState
from app.models.tags import TagSet
from app.services.realm_service import get_realm_config

_GRADE_SCORE = {
    "凡品": 0.25,
    "灵品": 0.5,
    "玄品": 0.75,
    "仙品": 1.0,
}

_ENDING_BONUS = {
    "飞升成仙": 1.0,
    "功德圆满": 0.8,
    "寿终正寝": 0.5,
}
_ENDING_BONUS_DEFAULT = 0.3

_GRADE_THRESHOLDS: list[tuple[int, str]] = [
    (95, "SSS"),
    (85, "SS"),
    (75, "S"),
    (60, "A"),
    (40, "B"),
    (20, "C"),
    (0, "D"),
]

_MAX_REALM_ORDER = 8  # 渡劫飞升 (YAML order 9 → 0-indexed 8)


def _get_realm_order(realm: str) -> int:
    """Get 0-indexed realm order. Returns 0 for unknown realms."""
    config = get_realm_config(realm)
    if config is None:
        return 0
    return config["order"] - 1


def _has_infinite_lifespan(realm: str) -> bool:
    """Check if the realm config has "无限" lifespan (渡劫飞升)."""
    config = get_realm_config(realm)
    if config is None:
        return False
    return config.get("lifespan") == "无限"


def _calculate_tag_score(tags: TagSet | None) -> float:
    """Calculate bonus score from character tags.

    - Tag variety bonus: 2 points per distinct active category (max 8)
    - Master lost bond: +5 points (tragic hero ending weight)
    """
    if not tags:
        return 0.0

    categories = {t.category for t in tags.tags if t.is_active}
    tag_bonus = len(categories) * 2.0
    tag_bonus = min(tag_bonus, 8.0)

    master_lost = tags.get_by_key("bond_master_lost")
    if master_lost:
        tag_bonus += 5.0

    return tag_bonus


def determine_ending(
    player_state: PlayerState,
    age: int,
    ascended: bool = False,
    tags: TagSet | None = None,
) -> str:
    """Determine ending type from player state and game context.

    MVP triggers 3 of 8 endings:
    - "飞升成仙"  — 渡劫成功 (ascended=True)
    - "功德圆满"  — natural death at high realm (realm >= 合体)
    - "寿终正寝"  — default natural death
    """
    if ascended:
        return "飞升成仙"

    if tags:
        master_lost = tags.get_by_key("bond_master_lost")
        if master_lost:
            return "道心破碎"

    # Infinite lifespan (渡劫飞升) prevents natural death endings
    if _has_infinite_lifespan(player_state.realm):
        return "寿终正寝"

    lifespan = player_state.lifespan
    if age >= lifespan:
        realm_order = _get_realm_order(player_state.realm)
        if realm_order >= 6:  # 合体 (YAML order 7 → 0-indexed 6)
            return "功德圆满"
        return "寿终正寝"

    return "寿终正寝"


def calculate_score(
    player_state: PlayerState,
    ending: str,
    age: int,
    technique_grades: list[str] | None = None,
    tags: TagSet | None = None,
) -> int:
    """Calculate final score (0-100) from 5 dimensions.

    Formula:
      - 境界分 (50%): (realm_order / max_order) * 50
      - 寿命分 (20%): min(age / lifespan, 1.0) * 20
      - 功法分 (20%): avg_technique_grade_score * 20
      - 结局分 (10%): ending_bonus * 10
      - 标签分 (up to 13): tag variety + master_lost bonus

    technique_grades are explicit strings like "凡品"/"灵品"/"玄品"/"仙品".
    Pass empty list for no techniques.
    """
    if technique_grades is None:
        technique_grades = []

    realm_order = _get_realm_order(player_state.realm)
    realm_component = (realm_order / _MAX_REALM_ORDER) * 50

    if _has_infinite_lifespan(player_state.realm):
        lifespan_component = 20.0
    else:
        lifespan = player_state.lifespan
        ratio = age / lifespan if lifespan > 0 else 1.0
        lifespan_component = min(ratio, 1.0) * 20

    if technique_grades:
        scores = [_GRADE_SCORE.get(g, 0.0) for g in technique_grades]
        avg = sum(scores) / len(scores)
    else:
        avg = 0.0
    technique_component = avg * 20

    bonus = _ENDING_BONUS.get(ending, _ENDING_BONUS_DEFAULT)
    ending_component = bonus * 10

    tag_component = _calculate_tag_score(tags)

    total = (
        realm_component
        + lifespan_component
        + technique_component
        + ending_component
        + tag_component
    )
    return max(0, min(100, round(total)))


def get_grade(score: int) -> str:
    """Map numeric score to letter grade."""
    for threshold, grade in _GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "D"
