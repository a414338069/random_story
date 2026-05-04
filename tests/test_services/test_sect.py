"""Tests for sect system (Task 7)."""

import pytest

from app.services.sect_service import (
    load_sects,
    check_join_conditions,
    get_sect_techniques,
)


# ---------------------------------------------------------------------------
# load_sects()
# ---------------------------------------------------------------------------


def test_load_sects_returns_4():
    sects = load_sects()
    assert len(sects) == 4


def test_all_sects_have_required_fields():
    sects = load_sects()
    required = {"name", "type", "weapon", "attribute", "join_conditions", "techniques"}
    for s in sects:
        assert required.issubset(s.keys()), f"Sect {s.get('name', '?')} missing fields"


def test_sect_names():
    sects = load_sects()
    names = [s["name"] for s in sects]
    assert "万剑山庄" in names
    assert "逍遥派" in names
    assert "金刚寺" in names
    assert "散修" in names


def test_sect_types():
    """万剑山庄/逍遥派/金刚寺 are type 门派, 散修 is type 散修."""
    sects = {s["name"]: s for s in load_sects()}
    assert sects["万剑山庄"]["type"] == "门派"
    assert sects["逍遥派"]["type"] == "门派"
    assert sects["金刚寺"]["type"] == "门派"
    assert sects["散修"]["type"] == "散修"


def test_each_sect_has_techniques_list():
    sects = load_sects()
    for s in sects:
        assert isinstance(s["techniques"], list)
        for tech in s["techniques"]:
            assert "name" in tech
            assert "grade" in tech
            assert "attribute" in tech


# ---------------------------------------------------------------------------
# check_join_conditions()
# ---------------------------------------------------------------------------


class TestWanjianShanzhuang:
    """万剑山庄: rootBone≥3 OR comprehension≥3."""

    def test_join_root_bone_meets_requirement(self):
        attrs = {"rootBone": 3, "comprehension": 2, "mindset": 1, "luck": 4}
        assert check_join_conditions(attrs, "万剑山庄") is True

    def test_join_comprehension_meets_requirement(self):
        attrs = {"rootBone": 2, "comprehension": 3, "mindset": 3, "luck": 2}
        assert check_join_conditions(attrs, "万剑山庄") is True

    def test_join_both_meet_requirement(self):
        attrs = {"rootBone": 4, "comprehension": 3, "mindset": 2, "luck": 1}
        assert check_join_conditions(attrs, "万剑山庄") is True

    def test_join_neither_meets_requirement(self):
        attrs = {"rootBone": 2, "comprehension": 2, "mindset": 4, "luck": 2}
        assert check_join_conditions(attrs, "万剑山庄") is False


class TestXiaoyaopai:
    """逍遥派: comprehension≥4."""

    def test_join_comprehension_meets_requirement(self):
        attrs = {"rootBone": 2, "comprehension": 4, "mindset": 2, "luck": 2}
        assert check_join_conditions(attrs, "逍遥派") is True

    def test_join_comprehension_above_requirement(self):
        attrs = {"rootBone": 1, "comprehension": 5, "mindset": 2, "luck": 2}
        assert check_join_conditions(attrs, "逍遥派") is True

    def test_join_comprehension_below_requirement(self):
        attrs = {"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2}
        assert check_join_conditions(attrs, "逍遥派") is False

    def test_join_comprehension_zero(self):
        attrs = {"rootBone": 4, "comprehension": 0, "mindset": 3, "luck": 3}
        assert check_join_conditions(attrs, "逍遥派") is False


class TestJingangsi:
    """金刚寺: rootBone≥4 AND mindset≥3."""

    def test_join_both_meet_requirement(self):
        attrs = {"rootBone": 4, "comprehension": 1, "mindset": 3, "luck": 2}
        assert check_join_conditions(attrs, "金刚寺") is True

    def test_join_root_bone_insufficient(self):
        attrs = {"rootBone": 3, "comprehension": 2, "mindset": 3, "luck": 2}
        assert check_join_conditions(attrs, "金刚寺") is False

    def test_join_mindset_insufficient(self):
        attrs = {"rootBone": 5, "comprehension": 2, "mindset": 2, "luck": 1}
        assert check_join_conditions(attrs, "金刚寺") is False

    def test_join_both_insufficient(self):
        attrs = {"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2}
        assert check_join_conditions(attrs, "金刚寺") is False


class TestSanxiu:
    """散修: always True."""

    def test_sanxiu_always_joins(self):
        attrs = {"rootBone": 0, "comprehension": 0, "mindset": 0, "luck": 10}
        assert check_join_conditions(attrs, "散修") is True

    def test_sanxiu_joins_with_any_attributes(self):
        attrs = {"rootBone": 4, "comprehension": 3, "mindset": 2, "luck": 1}
        assert check_join_conditions(attrs, "散修") is True


def test_check_conditions_unknown_sect():
    """Unknown sect name returns False."""
    attrs = {"rootBone": 5, "comprehension": 2, "mindset": 2, "luck": 1}
    assert check_join_conditions(attrs, "不存在的门派") is False


# ---------------------------------------------------------------------------
# get_sect_techniques()
# ---------------------------------------------------------------------------


def test_wanjianshanzhuang_techniques():
    techniques = get_sect_techniques("万剑山庄")
    assert len(techniques) == 1
    assert techniques[0]["name"] == "万剑诀"
    assert techniques[0]["grade"] == "灵品"
    assert techniques[0]["attribute"] == "金"


def test_xiaoyaopai_techniques():
    techniques = get_sect_techniques("逍遥派")
    assert len(techniques) == 1
    assert techniques[0]["name"] == "逍遥游"
    assert techniques[0]["grade"] == "灵品"
    assert techniques[0]["attribute"] == "水"


def test_jingangsi_techniques():
    techniques = get_sect_techniques("金刚寺")
    assert len(techniques) == 1
    assert techniques[0]["name"] == "金刚不坏体"
    assert techniques[0]["grade"] == "灵品"
    assert techniques[0]["attribute"] == "土"


def test_sanxiu_techniques_empty():
    techniques = get_sect_techniques("散修")
    assert techniques == []


def test_get_techniques_unknown_sect():
    techniques = get_sect_techniques("不存在的门派")
    assert techniques == []
