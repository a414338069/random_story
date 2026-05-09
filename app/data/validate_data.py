import yaml
from pathlib import Path

EVENTS_DIR = Path(__file__).parent / "events"
VALID_TYPES = {"daily", "adventure", "bottleneck", "narrative", "combat", "social", "economy", "emotional", "heavenly", "fortune", "sect", "stones", "explore", "birth", "childhood", "youth"}
REALMS = ["凡人", "炼气", "筑基", "金丹", "元婴", "化神", "合体", "大乘", "渡劫飞升"]
TIER_NAMES = {"低阶", "中阶", "高阶"}
KNOWN_OPTIONAL = {"scenarios", "trigger_tags", "event_tier", "narrative_only", "realm_narratives", "realm_prompt_templates", "realm_default_options", "realm_scale"}

def validate_all_templates() -> bool:
    errors = []
    templates = []
    for f in sorted(EVENTS_DIR.glob("*.yaml")):
        if f.name.startswith("_test_"):
            continue
        with open(f, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            errors.append(f"{f.name}: not a dict")
            continue
        for key in ("id", "type", "title", "fallback_narrative", "default_options", "weight", "trigger_conditions", "prompt_template"):
            if key not in data:
                errors.append(f"{f.name}: missing {key}")
        if "scenarios" in data and not isinstance(data["scenarios"], list):
            errors.append(f"{f.name}: scenarios must be a list")
        if "trigger_tags" in data and not isinstance(data["trigger_tags"], dict):
            errors.append(f"{f.name}: trigger_tags must be a dict")
        if "event_tier" in data and not isinstance(data["event_tier"], str):
            errors.append(f"{f.name}: event_tier must be a string")
        if data.get("type") not in VALID_TYPES:
            errors.append(f"{f.name}: invalid type {data.get('type')}")
        narr = data.get("fallback_narrative", "")
        if len(narr) < 20:
            errors.append(f"{f.name}: fallback_narrative too short ({len(narr)} chars)")
        opts = data.get("default_options", [])
        is_narrative_only = data.get("narrative_only", False)
        if is_narrative_only:
            if len(opts) != 0:
                errors.append(f"{f.name}: narrative_only event should have empty options")
        else:
            if not (2 <= len(opts) <= 4):
                errors.append(f"{f.name}: options count {len(opts)} not in 2-4")

        realm_narratives = data.get("realm_narratives", {})
        if realm_narratives:
            for key in realm_narratives:
                if key not in REALMS and key not in TIER_NAMES:
                    errors.append(f"{f.name}: realm_narratives key '{key}' is not a valid realm or tier name")

        realm_prompt_templates = data.get("realm_prompt_templates", {})
        if realm_prompt_templates:
            for key in realm_prompt_templates:
                if key not in REALMS and key not in TIER_NAMES:
                    errors.append(f"{f.name}: realm_prompt_templates key '{key}' is not a valid realm or tier name")

        realm_default_options = data.get("realm_default_options", {})
        if realm_default_options:
            for tier_key, options_list in realm_default_options.items():
                if tier_key not in REALMS and tier_key not in TIER_NAMES:
                    errors.append(f"{f.name}: realm_default_options key '{tier_key}' is not a valid realm or tier name")
                if not isinstance(options_list, list):
                    errors.append(f"{f.name}: realm_default_options.{tier_key} is not a list")
                else:
                    for i, opt in enumerate(options_list):
                        if not isinstance(opt, dict):
                            errors.append(f"{f.name}: realm_default_options.{tier_key}[{i}] is not a dict")
                        else:
                            if "id" not in opt:
                                errors.append(f"{f.name}: realm_default_options.{tier_key}[{i}] missing 'id'")
                            if "text" not in opt:
                                errors.append(f"{f.name}: realm_default_options.{tier_key}[{i}] missing 'text'")

        realm_scale = data.get("realm_scale", {})
        if realm_scale:
            scale_type = realm_scale.get("type")
            if scale_type not in ("tier", "realm"):
                errors.append(f"{f.name}: realm_scale type must be 'tier' or 'realm', got '{scale_type}'")
            for key, value in realm_scale.items():
                if key == "type":
                    continue
                if not isinstance(value, (int, float)) or value <= 0:
                    errors.append(f"{f.name}: realm_scale.{key} must be a positive number, got {value}")

        templates.append(data)

    for realm in REALMS:
        has_daily = False
        for t in templates:
            if t.get("type") != "daily":
                continue
            tc = t.get("trigger_conditions", {})
            if tc.get("min_realm", "") <= realm <= tc.get("max_realm", ""):
                has_daily = True
                break
        if not has_daily:
            errors.append(f"Realm {realm} has no daily event")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return False
    print(f"All {len(templates)} templates validated OK")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if validate_all_templates() else 1)
