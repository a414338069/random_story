"""Realm service — load, query, and validate realm configurations."""

import os

import yaml

_REALMS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "realms.yaml"
)

_realms_cache = None


def load_realms() -> list[dict]:
    """Load all realm configs from YAML. Result is cached."""
    global _realms_cache
    if _realms_cache is not None:
        return _realms_cache
    with open(_REALMS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _realms_cache = data.get("realms", [])
    return _realms_cache


def get_realm_config(name: str) -> dict | None:
    """Get a single realm config by name. Returns None if not found."""
    realms = load_realms()
    for r in realms:
        if r["name"] == name:
            return r
    return None


def get_stage_name(realm: str, progress: float) -> str | None:
    """Get the current sub-stage name based on progress (0.0–1.0)."""
    config = get_realm_config(realm)
    if config is None:
        return None
    stages = config.get("stages")
    if not stages:
        return None
    idx = int(progress * len(stages))
    if idx >= len(stages):
        idx = len(stages) - 1
    return stages[idx]


def can_breakthrough(cultivation: int, config: dict) -> bool:
    """Check if cultivation meets the breakthrough requirement."""
    req = config.get("cultivation_req")
    if req is None:
        return False
    return cultivation >= req


def get_next_realm(current: str) -> str | None:
    """Get the next realm name, or None if current is the highest realm."""
    config = get_realm_config(current)
    if config is None:
        return None
    next_order = config["order"] + 1
    realms = load_realms()
    for r in realms:
        if r["order"] == next_order:
            return r["name"]
    return None
