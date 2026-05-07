"""Tests for realm system (Task 6)."""

import pytest

from app.services.realm_service import (
    load_realms,
    get_realm_config,
    get_stage_name,
    can_breakthrough,
    get_next_realm,
)


# ---------------------------------------------------------------------------
# load_realms()
# ---------------------------------------------------------------------------


def test_load_realms_returns_9():
    realms = load_realms()
    assert len(realms) == 9


def test_all_realms_have_required_fields():
    realms = load_realms()
    required = {
        "name", "order", "stages", "lifespan", "time_span",
        "cultivation_req", "spirit_stone_cap", "technique_slots",
    }
    for r in realms:
        assert required.issubset(r.keys()), f"Realm {r.get('name', '?')} missing fields"


def test_all_realm_names_in_order():
    realms = load_realms()
    expected = ["凡人", "炼气", "筑基", "金丹", "元婴", "化神", "合体", "大乘", "渡劫飞升"]
    names = [r["name"] for r in realms]
    assert names == expected


def test_realm_orders_are_sequential():
    realms = load_realms()
    for i, r in enumerate(realms, start=1):
        assert r["order"] == i, f"{r['name']} should have order {i}"


def test_realm_stages_are_list_or_none():
    realms = load_realms()
    for r in realms:
        assert r["stages"] is None or isinstance(r["stages"], list), \
            f"{r['name']} stages should be list or None"
        if isinstance(r["stages"], list):
            assert len(r["stages"]) > 0, f"{r['name']} has empty stages"


# ---------------------------------------------------------------------------
# Specific realm configs
# ---------------------------------------------------------------------------


def test_mortal_config():
    r = get_realm_config("凡人")
    assert r["lifespan"] == 80
    assert r["time_span"] == 1
    assert r["stages"] is None
    assert r["cultivation_req"] == 0


def test_liangqi_config():
    r = get_realm_config("炼气")
    assert r["time_span"] == 1
    assert r["lifespan"] == 120
    assert r["stages"] == [
        "1层", "2层", "3层", "4层", "5层", "6层", "7层", "8层", "9层",
    ]
    assert r["cultivation_req"] == 100


def test_zhuji_config():
    r = get_realm_config("筑基")
    assert r["time_span"] == 1
    assert r["lifespan"] == 200
    assert r["stages"] == ["初期", "中期", "后期", "大圆满"]
    assert r["cultivation_req"] == 300


def test_jindan_config():
    r = get_realm_config("金丹")
    assert r["time_span"] == 10
    assert r["lifespan"] == 500
    assert r["cultivation_req"] == 1000


def test_yuanying_config():
    r = get_realm_config("元婴")
    assert r["time_span"] == 20
    assert r["lifespan"] == 1000
    assert r["cultivation_req"] == 3000


def test_huashen_config():
    r = get_realm_config("化神")
    assert r["time_span"] == 50
    assert r["lifespan"] == 3000
    assert r["cultivation_req"] == 10000


def test_heti_config():
    r = get_realm_config("合体")
    assert r["time_span"] == 100
    assert r["lifespan"] == 8000
    assert r["cultivation_req"] == 30000


def test_dacheng_config():
    r = get_realm_config("大乘")
    assert r["time_span"] == 200
    assert r["lifespan"] == 20000
    assert r["cultivation_req"] == 100000


def test_dujie_feisheng_config():
    r = get_realm_config("渡劫飞升")
    assert r["time_span"] is None
    assert r["lifespan"] == "无限"
    assert r["stages"] is None
    assert r["cultivation_req"] is None
    assert r["spirit_stone_cap"] is None
    assert r["technique_slots"] is None


# ---------------------------------------------------------------------------
# get_stage_name()
# ---------------------------------------------------------------------------


def test_mortal_no_stage():
    assert get_stage_name("凡人", 0.5) is None


def test_liangqi_stage_mapping():
    assert get_stage_name("炼气", 0.0) == "1层"
    assert get_stage_name("炼气", 0.1) == "1层"
    assert get_stage_name("炼气", 0.15) == "2层"
    assert get_stage_name("炼气", 0.5) == "5层"
    assert get_stage_name("炼气", 0.95) == "9层"
    assert get_stage_name("炼气", 1.0) == "9层"


def test_zhuji_stage_mapping():
    assert get_stage_name("筑基", 0.0) == "初期"
    assert get_stage_name("筑基", 0.2) == "初期"
    assert get_stage_name("筑基", 0.25) == "中期"
    assert get_stage_name("筑基", 0.5) == "后期"
    assert get_stage_name("筑基", 0.75) == "大圆满"
    assert get_stage_name("筑基", 1.0) == "大圆满"


def test_jindan_stage_mapping():
    assert get_stage_name("金丹", 0.3) == "中期"
    assert get_stage_name("金丹", 0.6) == "后期"


def test_dujie_no_stage():
    assert get_stage_name("渡劫飞升", 0.5) is None


def test_stage_name_unknown_realm():
    assert get_stage_name("不存在", 0.5) is None


# ---------------------------------------------------------------------------
# can_breakthrough()
# ---------------------------------------------------------------------------


def test_can_breakthrough_below_req():
    config = get_realm_config("炼气")
    assert can_breakthrough(99, config) is False


def test_can_breakthrough_at_req():
    config = get_realm_config("炼气")
    assert can_breakthrough(100, config) is True


def test_can_breakthrough_above_req():
    config = get_realm_config("炼气")
    assert can_breakthrough(200, config) is True


def test_can_breakthrough_mortal_always_true():
    config = get_realm_config("凡人")
    assert can_breakthrough(0, config) is True


def test_can_breakthrough_highest_realm():
    config = get_realm_config("渡劫飞升")
    assert can_breakthrough(999999, config) is False


# ---------------------------------------------------------------------------
# get_next_realm()
# ---------------------------------------------------------------------------


def test_get_next_realm_sequential():
    assert get_next_realm("凡人") == "炼气"
    assert get_next_realm("炼气") == "筑基"
    assert get_next_realm("筑基") == "金丹"
    assert get_next_realm("金丹") == "元婴"
    assert get_next_realm("大乘") == "渡劫飞升"


def test_get_next_realm_last_is_none():
    assert get_next_realm("渡劫飞升") is None


def test_get_next_realm_unknown():
    assert get_next_realm("不存在") is None


# ---------------------------------------------------------------------------
# get_realm_config()
# ---------------------------------------------------------------------------


def test_get_realm_config_valid():
    config = get_realm_config("凡人")
    assert config is not None
    assert config["name"] == "凡人"


def test_get_realm_config_invalid():
    assert get_realm_config("不存在") is None
