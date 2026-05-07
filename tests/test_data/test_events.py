import yaml
from pathlib import Path

EVENTS_DIR = Path(__file__).parent.parent.parent / "app" / "data" / "events"
VALID_TYPES = {"daily", "adventure", "bottleneck", "narrative", "combat", "economy", "emotional", "heavenly", "fortune", "sect", "social", "stones", "explore"}
REALMS = ["凡人", "炼气", "筑基", "金丹", "元婴", "化神", "合体", "大乘", "渡劫飞升"]
REQUIRED_KEYS = {"id", "type", "title", "fallback_narrative", "default_options", "weight", "trigger_conditions", "prompt_template"}

TEMPLATE_CACHE = None

def _load_templates():
    global TEMPLATE_CACHE
    if TEMPLATE_CACHE is not None:
        return TEMPLATE_CACHE
    templates = []
    for f in sorted(EVENTS_DIR.glob("*.yaml")):
        if f.name.startswith("_test_"):
            continue
        with open(f, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        data["_filename"] = f.name
        templates.append(data)
    TEMPLATE_CACHE = templates
    return templates


class TestEventTemplates:
    def test_all_files_parse(self):
        templates = _load_templates()
        assert len(templates) == 79, f"Expected 79 templates, got {len(templates)}"

    def test_required_fields_present(self):
        for t in _load_templates():
            missing = REQUIRED_KEYS - set(t.keys())
            assert not missing, f"{t['_filename']}: missing {missing}"

    def test_valid_types(self):
        for t in _load_templates():
            assert t["type"] in VALID_TYPES, f"{t['_filename']}: invalid type {t['type']}"

    def test_fallback_narrative_length(self):
        for t in _load_templates():
            narr = t["fallback_narrative"]
            assert len(narr) >= 20, f"{t['_filename']}: fallback_narrative too short ({len(narr)} chars)"

    def test_options_count(self):
        for t in _load_templates():
            opts = t["default_options"]
            # narrative_only events (birth/childhood) have 0 options
            if t.get("narrative_only"):
                assert len(opts) == 0, f"{t['_filename']}: narrative_only event should have 0 options, got {len(opts)}"
            else:
                assert 2 <= len(opts) <= 3, f"{t['_filename']}: options count {len(opts)} not in 2-3"

    def test_each_realm_has_daily(self):
        templates = _load_templates()
        for realm in REALMS:
            has_daily = False
            for t in templates:
                if t["type"] != "daily":
                    continue
                tc = t.get("trigger_conditions", {})
                min_r = tc.get("min_realm", "")
                max_r = tc.get("max_realm", "")
                if min_r <= realm <= max_r:
                    has_daily = True
                    break
            assert has_daily, f"Realm {realm} has no daily event"

    def test_bottleneck_005_special_props(self):
        templates = _load_templates()
        b5 = None
        for t in templates:
            if t["_filename"] == "bottleneck_005.yaml":
                b5 = t
                break
        assert b5 is not None, "bottleneck_005.yaml not found"
        tc = b5["trigger_conditions"]
        assert tc["min_age"] == 10, f"bottleneck_005 min_age should be 10, got {tc['min_age']}"
        assert tc["max_age"] == 12, f"bottleneck_005 max_age should be 12, got {tc['max_age']}"
        assert b5["weight"] == 10.0, f"bottleneck_005 weight should be 10.0, got {b5['weight']}"
        assert b5["type"] == "bottleneck", f"bottleneck_005 type should be bottleneck, got {b5['type']}"
