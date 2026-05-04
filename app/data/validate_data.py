import yaml
from pathlib import Path

EVENTS_DIR = Path(__file__).parent / "events"
VALID_TYPES = {"daily", "adventure", "bottleneck"}
REALMS = ["凡人", "练气", "筑基", "金丹", "元婴", "化神", "合体", "大乘", "渡劫飞升"]

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
        if data.get("type") not in VALID_TYPES:
            errors.append(f"{f.name}: invalid type {data.get('type')}")
        narr = data.get("fallback_narrative", "")
        if len(narr) < 20:
            errors.append(f"{f.name}: fallback_narrative too short ({len(narr)} chars)")
        opts = data.get("default_options", [])
        if not (2 <= len(opts) <= 3):
            errors.append(f"{f.name}: options count {len(opts)} not in 2-3")
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
