"""Talent card service — load, draw, validate."""

import logging
import os
import random
from collections import defaultdict

import yaml

logger = logging.getLogger(__name__)

_TALENTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "talents.yaml"
)

_talents_cache = None


def load_talents() -> list[dict]:
    """Load all 20 talent cards from YAML. Result is cached."""
    global _talents_cache
    if _talents_cache is not None:
        return _talents_cache
    with open(_TALENTS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _talents_cache = data["talents"]
    return _talents_cache


def _group_by_grade(talents: list[dict]) -> tuple[dict[str, list[dict]], dict[str, float]]:
    """Group talents by grade and extract grade → rarity mapping."""
    grades: dict[str, list[dict]] = defaultdict(list)
    grade_rarity: dict[str, float] = {}
    for t in talents:
        g = t["grade"]
        grades[g].append(t)
        grade_rarity[g] = t["rarity"]
    return grades, grade_rarity


def draw_cards(count: int = 3) -> list[dict]:
    """Draw *count* unique talent cards weighted by grade rarity.

    Algorithm: pick a grade by rarity weight, then pick uniformly within that grade.
    Guarantees no duplicate cards in a single draw.
    """
    talents = load_talents()
    grades, grade_rarity = _group_by_grade(talents)

    grade_names = list(grade_rarity.keys())
    weights = [grade_rarity[g] for g in grade_names]

    # Track used talent IDs to prevent duplicates
    used_ids: set[str] = set()
    drawn: list[dict] = []

    for _ in range(count):
        # Fallback: if all cards exhausted, break
        remaining = [t for t in talents if t["id"] not in used_ids]
        if not remaining:
            break

        # Pick a grade
        chosen_grade = random.choices(grade_names, weights=weights, k=1)[0]

        # Pick a card from that grade (skip if all already used)
        grade_candidates = [t for t in grades[chosen_grade] if t["id"] not in used_ids]

        if not grade_candidates:
            # Fallback: pick from any remaining card
            card = random.choice(remaining)
        else:
            card = random.choice(grade_candidates)

        used_ids.add(card["id"])
        drawn.append(card)

    return drawn


def validate_selection(talent_ids: list[str]) -> tuple[bool, str]:
    """Validate a talent selection.

    Returns (is_valid, error_message).
    """
    if len(talent_ids) != 3:
        return False, f"必须选择3张天赋卡，当前选择了{len(talent_ids)}张"

    talents = load_talents()
    valid_ids = {t["id"] for t in talents}
    for tid in talent_ids:
        if tid not in valid_ids:
            return False, f"无效的天赋卡ID: {tid}"

    return True, ""


def get_active_modifiers(talent_ids: list[str]) -> dict[str, float]:
    """Aggregate modifiers from all selected talents (additive).

    Sums modifiers of the same key across talents from effects,
    positive_effects, and negative_effects. Ignores talents
    with missing or empty effects, and skips non-numeric values.
    """
    talents = load_talents()
    talent_map = {t["id"]: t for t in talents}
    result: dict[str, float] = {}
    effect_sources = ("effects", "positive_effects", "negative_effects")
    for tid in talent_ids:
        talent = talent_map.get(tid)
        if not talent:
            continue
        for source in effect_sources:
            section = talent.get(source, {})
            if not isinstance(section, dict):
                continue
            modifiers = section.get("modifiers", {})
            if not isinstance(modifiers, dict):
                continue
            for key, val in modifiers.items():
                if isinstance(val, (int, float)):
                    result[key] = result.get(key, 0.0) + float(val)
                else:
                    logger.warning(
                        "非数值修饰符 talent=%s source=%s key=%s value=%s",
                        tid, source, key, val
                    )
    return result


def has_talent_effect(talent_ids: list[str], effect_key: str) -> bool:
    """Check if any talent has a specific effect key.

    Searches effects.modifiers, positive_effects.modifiers,
    and negative_effects.modifiers of all given talents.
    P2 reserved interface for dual-sided card logic.
    """
    talents = load_talents()
    talent_map = {t["id"]: t for t in talents}
    effect_sources = ("effects", "positive_effects", "negative_effects")
    for tid in talent_ids:
        talent = talent_map.get(tid)
        if not talent:
            continue
        for source in effect_sources:
            src_data = talent.get(source)
            if not isinstance(src_data, dict):
                continue
            modifiers = src_data.get("modifiers", {})
            if isinstance(modifiers, dict) and effect_key in modifiers:
                return True
    return False


def _apply_talent_attr_bonuses(talent_ids: list[str], base_attributes: dict) -> dict:
    """Apply attr_bonuses from talents to base attributes, clamped to [0, 10].

    Sums attr_bonuses from effects.attr_bonuses of each talent and adds
    them to base_attributes. Results are clamped to the valid [0, 10] range.
    Non-numeric bonus values are skipped with a warning.
    """
    talents = load_talents()
    talent_map = {t["id"]: t for t in talents}
    attr_keys = ("root_bone", "comprehension", "mindset", "luck")
    result = {k: int(base_attributes.get(k, 0)) for k in attr_keys}
    for tid in talent_ids:
        talent = talent_map.get(tid)
        if not talent:
            continue
        effects = talent.get("effects", {})
        if not isinstance(effects, dict):
            continue
        bonuses = effects.get("attr_bonuses", {})
        if not isinstance(bonuses, dict):
            continue
        for key in attr_keys:
            val = bonuses.get(key, 0)
            if isinstance(val, (int, float)):
                result[key] = result.get(key, 0) + int(val)
            else:
                logger.warning(
                    "非数值属性加成 talent=%s key=%s value=%s", tid, key, val
                )
    for key in attr_keys:
        result[key] = max(0, min(10, result[key]))
    return result
