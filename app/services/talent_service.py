"""Talent card service — load, draw, validate."""

import os
import random
from collections import defaultdict

import yaml

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
