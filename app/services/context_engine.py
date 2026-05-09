"""Context engine — maps player tags and state to scenario pools for template selection.

Bridges the gap between the tag system (app/models/tags.py) and the event engine
(app/services/event_engine.py). The scenario pool is used as a second filtering layer
after filter_templates().
"""

from __future__ import annotations

from app.models.tags import TagCategory, TagSet

_BASE_POOL: list[str] = ["generic_daily"]


def determine_scenario_pool(tags: TagSet | None, player_state: dict | None) -> list[str]:
    """Map player tags and state to a list of scenario identifiers.

    Args:
        tags: The player's TagSet. May be None or empty.
        player_state: A dict with at least "age". May be None.

    Returns:
        A list of scenario identifier strings (e.g. ["generic_daily", "faction_万剑山庄"]).
        The base pool always includes "generic_daily".
    """
    scenarios: list[str] = ["generic_daily"]

    if tags is None or not tags.tags:
        return scenarios

    if player_state is None:
        player_state = {}

    # ── Faction identity ──
    faction_tag = tags.get_by_key("faction")
    if faction_tag is not None:
        faction_name = faction_tag.value.split("=")[-1]
        scenarios.append(f"faction_{faction_name}")
        scenarios.append("faction_life")
        if player_state.get("age", 0) >= 21:
            scenarios.append("faction_senior")

    # ── Skill-based scenarios ──
    skills = tags.get_by_category(TagCategory.SKILL)
    if skills:
        scenarios.append("has_technique")

    # ── Relationship-based scenarios ──
    bonds = tags.get_by_category(TagCategory.BOND)
    if bonds:
        has_companion = any("companion" in b.key for b in bonds)
        has_rival = any("rival" in b.key for b in bonds)
        if has_companion:
            scenarios.append("has_companion")
        if has_rival:
            scenarios.append("has_rival")

    # ── State-based scenarios ──
    states = tags.get_by_category(TagCategory.STATE)
    if states:
        if any("injured" in s.key for s in states):
            scenarios.append("injured")
        if any("blessed" in s.key for s in states):
            scenarios.append("blessed")
        if any("hunted" in s.key for s in states):
            scenarios.append("hunted")

    # ── Memory-based scenarios ──
    if bonds and any("childhood_memory" in m.key for m in bonds):
        scenarios.append("childhood_special")

    return scenarios


def match_scenarios(templates: list[dict], scenarios: list[str]) -> list[dict]:
    """Filter templates to those matching at least one scenario from the pool.

    Args:
        templates: List of template dicts, each optionally containing a "scenarios" field.
        scenarios: The active scenario pool (from determine_scenario_pool).

    Returns:
        Templates that either have no scenarios field (pass-through) or have at least
        one scenario overlapping with the pool.

    Rules:
        - Templates with an empty or missing "scenarios" field always match.
        - Templates with scenarios match if at least one scenario appears in the pool.
    """
    scenario_set = set(scenarios)
    matched: list[dict] = []

    for t in templates:
        template_scenarios = t.get("scenarios", [])
        if not isinstance(template_scenarios, list):
            template_scenarios = []
        if not template_scenarios or scenario_set.intersection(template_scenarios):
            matched.append(t)

    return matched
