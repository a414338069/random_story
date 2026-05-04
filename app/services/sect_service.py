"""Sect service — load, query, and validate sect configurations."""

import os

import yaml

_SECTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "sects.yaml"
)

_sects_cache = None


def load_sects() -> list[dict]:
    """Load all sect configs from YAML. Result is cached."""
    global _sects_cache
    if _sects_cache is not None:
        return _sects_cache
    with open(_SECTS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _sects_cache = data.get("sects", [])
    return _sects_cache


def _get_sect_by_name(name: str) -> dict | None:
    """Get a single sect config by name. Returns None if not found."""
    sects = load_sects()
    for s in sects:
        if s["name"] == name:
            return s
    return None


def check_join_conditions(attributes: dict, sect_name: str) -> bool:
    """Check if a player meets the join conditions for a given sect.

    Args:
        attributes: Dict with camelCase keys (rootBone, comprehension, mindset, luck).
        sect_name: The name of the sect to check.

    Returns:
        True if the player meets the join conditions, False otherwise.
    """
    sect = _get_sect_by_name(sect_name)
    if sect is None:
        return False

    conditions = sect["join_conditions"]
    logic = conditions["logic"]

    if logic == "ALWAYS":
        return True

    if logic == "SINGLE":
        for attr_key, condition in conditions.items():
            if attr_key == "logic":
                continue
            val = attributes.get(attr_key, 0)
            op = condition["operator"]
            req = condition["value"]
            if op == ">=" and val >= req:
                return True
            if op == ">" and val > req:
                return True
        return False

    if logic == "OR":
        results = []
        for attr_key, condition in conditions.items():
            if attr_key == "logic":
                continue
            val = attributes.get(attr_key, 0)
            op = condition["operator"]
            req = condition["value"]
            if op == ">=":
                results.append(val >= req)
            elif op == ">":
                results.append(val > req)
            else:
                results.append(False)
        return any(results)

    if logic == "AND":
        for attr_key, condition in conditions.items():
            if attr_key == "logic":
                continue
            val = attributes.get(attr_key, 0)
            op = condition["operator"]
            req = condition["value"]
            if op == ">=":
                if not (val >= req):
                    return False
            elif op == ">":
                if not (val > req):
                    return False
            else:
                return False
        return True

    return False


def get_sect_techniques(sect_name: str) -> list[dict]:
    """Get the techniques granted by joining a sect.

    Returns:
        A list of technique dicts, or an empty list if sect not found or no techniques.
    """
    sect = _get_sect_by_name(sect_name)
    if sect is None:
        return []
    return sect.get("techniques", [])
