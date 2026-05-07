"""Event engine — load, filter, weight, and select story events."""

import copy
import glob
import os
import random

import yaml

from app.services.realm_service import get_realm_config

REALM_TIER_MAP = {
    1: "低阶", 2: "低阶", 3: "低阶",
    4: "中阶", 5: "中阶", 6: "中阶",
    7: "高阶", 8: "高阶", 9: "高阶",
}

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


def _get_realm_tier(realm_name: str) -> str | None:
    """Map a realm name to its tier category via REALM_TIER_MAP."""
    order = _get_realm_order(realm_name)
    if order is None:
        return None
    return REALM_TIER_MAP.get(order)


def _get_realm_value(values: dict, player_realm: str) -> str | None:
    """Look up a value by realm: first exact match, then tier fallback."""
    if not values:
        return None
    # 1) Exact realm match
    if player_realm in values:
        return values[player_realm]
    # 2) Tier fallback
    tier = _get_realm_tier(player_realm)
    if tier and tier in values:
        return values[tier]
    return None


def _apply_consequence_scale(
    options: list[dict], scale_config: dict, player_realm: str
) -> list[dict]:
    """Deep-copy options and scale numeric consequence values."""
    if not options or not scale_config:
        return copy.deepcopy(options)

    # Determine the scale factor
    scale_type = scale_config.get("type", "tier")
    if scale_type == "realm":
        factor = scale_config.get(player_realm, 1.0)
    else:
        tier = _get_realm_tier(player_realm)
        factor = scale_config.get(tier, 1.0) if tier else 1.0

    # Apply scaling to a deep copy
    scaled = copy.deepcopy(options)
    for opt in scaled:
        consequences = opt.get("consequences", {})
        if not consequences:
            continue
        for key, value in consequences.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                consequences[key] = value * factor
    return scaled


class _SafeFormatDict(dict):
    """dict subclass that returns the placeholder itself for missing keys."""

    def __missing__(self, key):
        return "{" + str(key) + "}"


def _safe_format(text: str, **kwargs) -> str:
    """Format a string safely: unknown placeholders are left as-is."""
    return text.format_map(_SafeFormatDict(kwargs))


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
        # requires_any_faction: 玩家必须已经加入某个门派（通用宗门模板如 sect_001/002/003）
        if cond.get("requires_any_faction", False) and not player_faction:
            continue

        # Life-stage filtering
        if player_age < 12:
            if not t.get("narrative_only", False):
                continue
        elif player_age <= 15:
            if t.get("type") == "adventure":
                continue

        if t.get("type") == "bottleneck":
            last_bt = player_state.get("_breakthrough_event_count", -999)
            current_ec = player_state.get("event_count", 0)
            if current_ec - last_bt < 3:
                continue

        result.append(t)

    return result


def calculate_weights(
    templates: list[dict], player_state: dict
) -> list[tuple[dict, float]]:
    luck = player_state.get("luck", 0)
    cultivation = player_state.get("cultivation", 0)
    realm = player_state.get("realm", "")
    player_age = player_state.get("age", 0)

    youth_weight_factor = 0.7 if 12 <= player_age <= 15 else 1.0

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

        weight *= youth_weight_factor
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

    seen_ids: set[str] = set()
    if player_state:
        seen_ids = set(player_state.get("_seen_event_ids", []))

    templates, weights = zip(*weighted_templates) if weighted_templates else ([], [])
    templates_list = list(templates)
    weights_list = list(weights)

    # 优先选择未见过的模板：降低已见模板的权重
    if seen_ids:
        adjusted = []
        for t, w in zip(templates_list, weights_list):
            if t.get("id", "") in seen_ids:
                adjusted.append(w * 0.1)
            else:
                adjusted.append(w)
        weights_list = adjusted

    chosen = random.choices(templates_list, weights=weights_list, k=1)[0]
    return chosen


def build_event_context(template: dict, player_state: dict) -> dict:
    player_realm = player_state.get("realm", "")
    tier = _get_realm_tier(player_realm)
    fmt_kwargs = dict(
        realm=player_realm,
        age=player_state.get("age", 0),
        realm_variant=tier or player_realm,
    )

    # 1) Prompt — realm-specific override if available
    realm_prompts = template.get("realm_prompt_templates")
    raw_prompt = _get_realm_value(realm_prompts, player_realm) if realm_prompts else None
    if not raw_prompt:
        raw_prompt = template.get("prompt_template", "")
    prompt = _safe_format(raw_prompt, **fmt_kwargs)

    # 2) Fallback narrative — realm-specific override if available
    realm_narratives = template.get("realm_narratives")
    raw_fallback = _get_realm_value(realm_narratives, player_realm) if realm_narratives else None
    if not raw_fallback:
        raw_fallback = template.get("fallback_narrative", "")
    fallback = _safe_format(raw_fallback, **fmt_kwargs) if raw_fallback else ""

    # 3) Default options — realm-specific override if available
    realm_options = template.get("realm_default_options")
    default_options = (
        _get_realm_value(realm_options, player_realm) if realm_options else None
    )
    if not default_options:
        default_options = template.get("default_options", [])

    # 4) Consequence scaling
    realm_scale = template.get("realm_scale")
    if realm_scale:
        default_options = _apply_consequence_scale(default_options, realm_scale, player_realm)

    return {
        "title": template.get("title", ""),
        "event_type": template.get("type", ""),
        "prompt": prompt,
        "fallback_narrative": fallback,
        "default_options": default_options,
        "narrative_only": template.get("narrative_only", False),
        "player": player_state,
    }


def should_force_non_daily(
    consecutive_daily_count: int, threshold: int = 3
) -> bool:
    return consecutive_daily_count >= threshold
