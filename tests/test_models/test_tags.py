"""Tests for tag data model system."""

import pytest
from pydantic import ValidationError

from app.models.tags import (
    MAX_ACTIVE_TAGS,
    Tag,
    TagCategory,
    TagSet,
)


class TestTagCategory:
    def test_four_categories(self):
        assert len(TagCategory) == 4
        assert TagCategory.IDENTITY.value == "identity"
        assert TagCategory.SKILL.value == "skill"
        assert TagCategory.BOND.value == "bond"
        assert TagCategory.STATE.value == "state"

    def test_enum_membership(self):
        assert isinstance(TagCategory.IDENTITY, TagCategory)
        assert TagCategory("identity") == TagCategory.IDENTITY


class TestTag:
    def test_minimal_tag(self):
        tag = Tag(category=TagCategory.IDENTITY, key="sect_qingyun", value="青云门弟子")
        assert tag.category == TagCategory.IDENTITY
        assert tag.key == "sect_qingyun"
        assert tag.value == "青云门弟子"
        assert tag.years_active == -1
        assert tag.priority == 0
        assert tag.is_active is True

    def test_tag_with_all_fields(self):
        tag = Tag(
            category=TagCategory.STATE,
            key="poisoned",
            value="中毒",
            description="中了奇毒，修为难以精进",
            years_active=5,
            priority=8,
        )
        assert tag.description == "中了奇毒，修为难以精进"
        assert tag.years_active == 5
        assert tag.priority == 8

    def test_is_persistent_property(self):
        persistent = Tag(category=TagCategory.IDENTITY, key="t1", value="T1")
        assert persistent.is_persistent is True
        temporary = Tag(category=TagCategory.STATE, key="t2", value="T2", years_active=3)
        assert temporary.is_persistent is False

    def test_negative_priority_raises(self):
        with pytest.raises(ValidationError):
            Tag(category=TagCategory.IDENTITY, key="t", value="T", priority=-1)


class TestTagSet:
    def test_empty_tagset(self):
        ts = TagSet()
        assert ts.tags == []
        assert ts.get_by_category(TagCategory.IDENTITY) == []
        assert ts.get_by_key("nonexistent") is None

    def test_add_and_get_tag(self):
        ts = TagSet()
        tag = Tag(category=TagCategory.IDENTITY, key="sect_qingyun", value="青云门弟子")
        ts.add(tag)
        assert len(ts.tags) == 1
        assert ts.get_by_key("sect_qingyun") is tag

    def test_get_by_category_filters_correctly(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.IDENTITY, key="sect", value="青云门"))
        ts.add(Tag(category=TagCategory.SKILL, key="sword", value="剑法"))
        ts.add(Tag(category=TagCategory.STATE, key="buff", value="增益"))

        identity_tags = ts.get_by_category(TagCategory.IDENTITY)
        assert len(identity_tags) == 1
        assert identity_tags[0].key == "sect"

        state_tags = ts.get_by_category(TagCategory.STATE)
        assert len(state_tags) == 1
        assert state_tags[0].key == "buff"

    def test_remove_by_key(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.IDENTITY, key="sect", value="青云门弟子"))
        ts.remove("sect")
        assert ts.get_by_key("sect") is None
        assert len(ts.tags) == 0

    def test_remove_nonexistent_does_not_raise(self):
        ts = TagSet()
        ts.remove("nonexistent")
        assert len(ts.tags) == 0

    def test_update_existing_tag_by_key(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.SKILL, key="sword", value="剑法入门", priority=1))
        ts.add(Tag(category=TagCategory.SKILL, key="sword", value="剑法精通", priority=3))
        assert len(ts.tags) == 1
        tag = ts.get_by_key("sword")
        assert tag is not None
        assert tag.value == "剑法精通"
        assert tag.priority == 3


class TestTagAging:
    def test_age_tags_decrements_state_tags(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.STATE, key="poisoned", value="中毒", years_active=5))
        ts.age_tags(2)
        tag = ts.get_by_key("poisoned")
        assert tag is not None
        assert tag.years_active == 3

    def test_age_tags_removes_expired_tags(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.STATE, key="poisoned", value="中毒", years_active=3))
        ts.age_tags(5)
        assert ts.get_by_key("poisoned") is None

    def test_age_tags_ignores_persistent_tags(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.IDENTITY, key="sect", value="青云门弟子"))
        ts.age_tags(100)
        assert ts.get_by_key("sect") is not None

    def test_age_tags_exact_boundary(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.STATE, key="buff", value="增益", years_active=3))
        ts.age_tags(3)
        assert ts.get_by_key("buff") is None

    def test_age_tags_partial_some_expire_some_remain(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.STATE, key="short", value="短期", years_active=2))
        ts.add(Tag(category=TagCategory.STATE, key="long", value="长期", years_active=10))
        ts.age_tags(5)
        assert ts.get_by_key("short") is None
        long_tag = ts.get_by_key("long")
        assert long_tag is not None
        assert long_tag.years_active == 5


class TestContextString:
    def test_to_context_string_with_all_categories(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.IDENTITY, key="sect", value="青云门弟子"))
        ts.add(Tag(category=TagCategory.SKILL, key="sword", value="剑法入门"))
        ts.add(Tag(category=TagCategory.BOND, key="friend", value="与大师兄交好", priority=5))
        ts.add(Tag(category=TagCategory.STATE, key="poisoned", value="中毒", years_active=3))

        ctx = ts.to_context_string()
        assert "【角色标签】" in ctx
        assert "身份: 青云门弟子" in ctx
        assert "技能: 剑法入门" in ctx
        assert "羁绊: 与大师兄交好" in ctx
        assert "中毒(剩余3年)" in ctx

    def test_to_context_string_empty(self):
        ts = TagSet()
        ctx = ts.to_context_string()
        assert "身份: 无" in ctx
        assert "技能: 无" in ctx
        assert "羁绊: 无" in ctx
        assert "状态: 无" in ctx

    def test_bond_tags_sorted_by_priority_descending(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.BOND, key="f1", value="普通朋友", priority=1))
        ts.add(Tag(category=TagCategory.BOND, key="f2", value="至交好友", priority=10))
        ts.add(Tag(category=TagCategory.BOND, key="f3", value="泛泛之交", priority=0))

        ctx = ts.to_context_string()
        bond_line = [line for line in ctx.split("\n") if "羁绊:" in line][0]
        assert bond_line.index("至交好友") < bond_line.index("普通朋友") < bond_line.index("泛泛之交")

    def test_state_tags_with_years_remaining(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.STATE, key="s1", value="顿悟中", years_active=1))
        ts.add(Tag(category=TagCategory.STATE, key="s2", value="伤势恢复中", years_active=-1))

        ctx = ts.to_context_string()
        assert "顿悟中(剩余1年)" in ctx
        assert "伤势恢复中" in ctx
        assert "(剩余" in ctx


class TestLRUEviction:
    def test_evicts_state_tag_when_over_capacity(self):
        ts = TagSet()
        for i in range(MAX_ACTIVE_TAGS - 1):
            ts.add(Tag(category=TagCategory.IDENTITY, key=f"identity_{i}", value=f"标签{i}"))
        assert len(ts.tags) == MAX_ACTIVE_TAGS - 1

        ts.add(Tag(category=TagCategory.STATE, key="state_1", value="状态标签1"))
        assert len(ts.tags) == MAX_ACTIVE_TAGS

        ts.add(Tag(category=TagCategory.STATE, key="state_2", value="状态标签2"))
        assert len(ts.tags) == MAX_ACTIVE_TAGS
        assert ts.get_by_key("state_1") is None
        assert ts.get_by_key("state_2") is not None

    def test_evicts_lru_state_tag(self):
        ts = TagSet()
        for i in range(MAX_ACTIVE_TAGS - 2):
            ts.add(Tag(category=TagCategory.IDENTITY, key=f"identity_{i}", value=f"标签{i}"))

        ts.add(Tag(category=TagCategory.STATE, key="old_state", value="旧状态"))
        ts.get_by_key("old_state")
        ts.add(Tag(category=TagCategory.STATE, key="new_state", value="新状态"))

        assert len(ts.tags) == MAX_ACTIVE_TAGS

        ts.add(Tag(category=TagCategory.STATE, key="overflow", value="溢出"))
        assert len(ts.tags) == MAX_ACTIVE_TAGS
        assert ts.get_by_key("old_state") is None

    def test_no_eviction_when_under_capacity(self):
        ts = TagSet()
        for i in range(MAX_ACTIVE_TAGS - 5):
            ts.add(Tag(category=TagCategory.IDENTITY, key=f"t{i}", value=f"标签{i}"))
        ts.add(Tag(category=TagCategory.STATE, key="state_1", value="状态"))
        assert len(ts.tags) == MAX_ACTIVE_TAGS - 4


class TestTagSerialization:
    def test_tag_serialization_roundtrip(self):
        tag = Tag(
            category=TagCategory.STATE,
            key="poisoned",
            value="中毒",
            description="剧毒",
            years_active=5,
            priority=8,
        )
        data = tag.model_dump()
        restored = Tag.model_validate(data)
        assert restored.key == "poisoned"
        assert restored.years_active == 5
        assert restored.category == TagCategory.STATE

    def test_tagset_serialization_roundtrip(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.IDENTITY, key="sect", value="青云门"))
        ts.add(Tag(category=TagCategory.SKILL, key="sword", value="剑法", priority=3))

        data = ts.model_dump()
        restored = TagSet.model_validate(data)
        assert len(restored.tags) == 2
        sect_tag = restored.get_by_key("sect")
        sword_tag = restored.get_by_key("sword")
        assert sect_tag is not None
        assert sword_tag is not None
        assert sect_tag.value == "青云门"
        assert sword_tag.priority == 3

    def test_tagset_serialization_rebuilds_lru(self):
        ts = TagSet()
        ts.add(Tag(category=TagCategory.IDENTITY, key="sect", value="青云门"))

        data = ts.model_dump()
        restored = TagSet.model_validate(data)
        assert restored._lru_keys == ["sect"]
