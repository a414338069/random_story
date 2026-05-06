"""Event engine — load, filter, weight, and select story events."""

import glob
import os
import random

import yaml

from app.services.realm_service import get_realm_config

_EVENTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "events"
)

_templates_cache = None

FALLBACK_EVENT = {
    "id": "fallback",
    "type": "daily",
    "title": "平淡的一天",
    "trigger_conditions": {
        "min_realm": "凡人",
        "max_realm": "渡劫飞升",
        "min_age": 0,
        "max_age": 9999,
        "required_faction": None,
    },
    "weight": 1.0,
    "prompt_template": "你在修行中度过了一天。",
    "fallback_narrative": "你静静地修炼，修为有所增长。",
    "default_options": [
        {
            "id": "opt1",
            "text": "继续修炼",
            "consequences": {"cultivation_gain": 5, "age_advance": True},
        }
    ],
}


def load_templates() -> list[dict]:
    global _templates_cache
    if _templates_cache is not None:
        return _templates_cache
    templates = []
    pattern = os.path.join(_EVENTS_DIR, "*.yaml")
    for path in sorted(glob.glob(pattern)):
        filename = os.path.basename(path)
        if filename.startswith("_test_"):
            continue
        with open(path, "r", encoding="utf-8") as f:
            template = yaml.safe_load(f)
            if isinstance(template, dict):
                templates.append(template)
    _templates_cache = templates
    return _templates_cache


def _get_realm_order(realm_name: str) -> int | None:
    config = get_realm_config(realm_name)
    if config is None:
        return None
    return config.get("order")


def filter_templates(templates: list[dict], player_state: dict) -> list[dict]:
    player_realm = player_state.get("realm", "")
    player_age = player_state.get("age", 0)
    player_faction = player_state.get("faction", "")

    player_order = _get_realm_order(player_realm)
    if player_order is None:
        return []

    result = []
    for t in templates:
        cond = t.get("trigger_conditions", {})
        min_order = _get_realm_order(cond.get("min_realm", ""))
        max_order = _get_realm_order(cond.get("max_realm", ""))
        min_age = cond.get("min_age", 0)
        max_age = cond.get("max_age", 9999)
        req_faction = cond.get("required_faction")

        if min_order is not None and player_order < min_order:
            continue
        if max_order is not None and player_order > max_order:
            continue
        if player_age < min_age or player_age > max_age:
            continue
        if req_faction is not None and player_faction != req_faction:
            continue

        result.append(t)

    return result


def calculate_weights(
    templates: list[dict], player_state: dict
) -> list[tuple[dict, float]]:
    luck = player_state.get("luck", 0)
    cultivation = player_state.get("cultivation", 0)
    realm = player_state.get("realm", "")

    weighted = []
    for t in templates:
        event_type = t.get("type", "daily")
        if event_type == "daily":
            weight = 1.0
        elif event_type == "adventure":
            weight = 0.3 + luck * 0.05
        elif event_type == "bottleneck":
            realm_config = get_realm_config(realm)
            req = realm_config.get("cultivation_req") if realm_config else None
            if req is None or req == 0:
                weight = 1.0
            else:
                weight = 0.5 + (cultivation / req) * 0.5
        else:
            weight = 1.0

        weighted.append((t, weight))

    return weighted


def _build_quiet_year_event(player_state: dict) -> dict:
    """构建安静年事件——纯叙事推进，无选项。"""
    narratives = [
        "这一年风调雨顺，你在山中静修，虽无大事，但根基更加稳固。",
        "日子平静如水。你日出而作、日落而息，修行虽慢但踏实。",
        "山中无甲子，寒尽不知年。这一年平静得仿佛时间停滞。",
        "这一年过得波澜不惊，你在默默修行中度过。",
        "四季轮转，岁月静好。这一年没有特别的际遇，但也并非虚度。",
    ]
    return {
        "id": "quiet_year",
        "type": "daily",
        "title": "平静的一年",
        "trigger_conditions": {"min_realm": "凡人", "max_realm": "渡劫飞升", "min_age": 0, "max_age": 9999, "required_faction": None},
        "weight": 1.0,
        "prompt_template": "这一年没什么特别的事发生，你在安静中修炼...",
        "fallback_narrative": random.choice(narratives),
        "default_options": [],
        "narrative_only": True,
    }


def select_event(weighted_templates: list[tuple[dict, float]], player_state: dict | None = None) -> dict:
    if player_state:
        consecutive = player_state.get("_consecutive_events", 0)
        if consecutive >= 2 and random.random() < 0.25:
            return _build_quiet_year_event(player_state)
    if not weighted_templates:
        return FALLBACK_EVENT

    templates, weights = zip(*weighted_templates) if weighted_templates else ([], [])
    chosen = random.choices(list(templates), weights=list(weights), k=1)[0]
    return chosen


def build_event_context(template: dict, player_state: dict) -> dict:
    raw_prompt = template.get("prompt_template", "")
    prompt = raw_prompt.format(
        realm=player_state.get("realm", ""),
        age=player_state.get("age", 0),
    )

    return {
        "title": template.get("title", ""),
        "event_type": template.get("type", ""),
        "prompt": prompt,
        "fallback_narrative": template.get("fallback_narrative", ""),
        "default_options": template.get("default_options", []),
        "narrative_only": template.get("narrative_only", False),
        "player": player_state,
    }


def should_force_non_daily(
    consecutive_daily_count: int, threshold: int = 3
) -> bool:
    return consecutive_daily_count >= threshold
