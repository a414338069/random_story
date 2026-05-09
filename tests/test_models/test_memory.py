"""Tests for narrative memory model (StoryMemory & StoryMemorySet)."""

import pytest
from pydantic import ValidationError

from app.models.memory import MAX_MEMORIES, StoryMemory, StoryMemorySet


class TestStoryMemory:
    def test_minimal_memory(self):
        m = StoryMemory(event_id="evt_001", summary="获得一本功法", happened_at_age=16)
        assert m.event_id == "evt_001"
        assert m.summary == "获得一本功法"
        assert m.happened_at_age == 16
        assert m.tags_involved == []
        assert m.emotional_weight == 1.0

    def test_memory_with_all_fields(self):
        m = StoryMemory(
            event_id="evt_002",
            summary="击败妖兽，获得内丹",
            tags_involved=["beast", "combat"],
            happened_at_age=22,
            emotional_weight=3.5,
        )
        assert m.tags_involved == ["beast", "combat"]
        assert m.emotional_weight == 3.5

    def test_emotional_weight_validation_low(self):
        with pytest.raises(ValidationError):
            StoryMemory(event_id="evt_003", summary="小事", happened_at_age=10, emotional_weight=-0.1)

    def test_emotional_weight_validation_high(self):
        with pytest.raises(ValidationError):
            StoryMemory(event_id="evt_004", summary="大事", happened_at_age=20, emotional_weight=5.1)

    def test_emotional_weight_boundaries(self):
        m1 = StoryMemory(event_id="evt_005", summary="零", happened_at_age=1, emotional_weight=0.0)
        assert m1.emotional_weight == 0.0
        m2 = StoryMemory(event_id="evt_006", summary="极大", happened_at_age=50, emotional_weight=5.0)
        assert m2.emotional_weight == 5.0

    def test_summary_max_length(self):
        with pytest.raises(ValidationError):
            StoryMemory(
                event_id="evt_007",
                summary="a" * 101,
                happened_at_age=10,
            )

    def test_summary_exactly_100_chars(self):
        m = StoryMemory(
            event_id="evt_008",
            summary="a" * 100,
            happened_at_age=10,
        )
        assert len(m.summary) == 100


class TestStoryMemorySetAdd:
    def test_add_memory(self):
        sset = StoryMemorySet()
        m = StoryMemory(event_id="evt_001", summary="拜入师门", happened_at_age=16)
        sset.add(m)
        assert len(sset.memories) == 1
        assert sset.memories[0].event_id == "evt_001"

    def test_add_multiple_memories(self):
        sset = StoryMemorySet()
        for i in range(5):
            sset.add(StoryMemory(
                event_id=f"evt_{i}", summary=f"事件{i}", happened_at_age=10 + i,
            ))
        assert len(sset.memories) == 5

    def test_retention_max_memories(self):
        sset = StoryMemorySet()
        for i in range(MAX_MEMORIES):
            sset.add(StoryMemory(
                event_id=f"evt_{i}", summary=f"记忆{i}",
                happened_at_age=10 + i, emotional_weight=2.0,
            ))
        assert len(sset.memories) == MAX_MEMORIES

    def test_evict_lowest_emotional_weight(self):
        sset = StoryMemorySet()
        # Fill to MAX_MEMORIES with weight 1.0
        for i in range(MAX_MEMORIES):
            sset.add(StoryMemory(
                event_id=f"evt_{i}", summary=f"记忆{i}",
                happened_at_age=i, emotional_weight=1.0,
            ))
        # Add one more with higher weight — should evict one of the 1.0 ones
        sset.add(StoryMemory(
            event_id="evt_special", summary="特殊事件",
            happened_at_age=99, emotional_weight=5.0,
        ))
        assert len(sset.memories) == MAX_MEMORIES
        assert any(m.event_id == "evt_special" for m in sset.memories)
        # There must be exactly one 1.0-weight memory evicted
        assert sum(1 for m in sset.memories if m.emotional_weight == 1.0) == MAX_MEMORIES - 1

    def test_evict_tiebreaker_oldest_age(self):
        sset = StoryMemorySet()
        # Fill to capacity with all weight=1.0
        for i in range(MAX_MEMORIES):
            sset.add(StoryMemory(
                event_id=f"evt_{i}", summary=f"记忆{i}",
                happened_at_age=i, emotional_weight=1.0,
            ))
        # The oldest is evt_0 (age 0). Add a new one to trigger eviction.
        sset.add(StoryMemory(
            event_id="evt_new", summary="新记忆",
            happened_at_age=100, emotional_weight=1.0,
        ))
        assert len(sset.memories) == MAX_MEMORIES
        # evt_0 was the oldest at weight 1.0 → evicted
        assert all(m.event_id != "evt_0" for m in sset.memories)
        assert any(m.event_id == "evt_new" for m in sset.memories)

    def test_evict_prefers_lowest_weight_not_oldest(self):
        sset = StoryMemorySet()
        # Fill to MAX_MEMORIES - 1 with weight 1.0
        for i in range(MAX_MEMORIES - 1):
            sset.add(StoryMemory(
                event_id=f"normal_{i}", summary=f"普通{i}",
                happened_at_age=i, emotional_weight=1.0,
            ))
        # Add one low-weight memory (should be evicted first)
        sset.add(StoryMemory(
            event_id="trivial", summary="琐事",
            happened_at_age=100, emotional_weight=0.1,
        ))
        assert len(sset.memories) == MAX_MEMORIES
        # Add another — should evict "trivial" (weight 0.1) not a normal one
        sset.add(StoryMemory(
            event_id="important", summary="重要事件",
            happened_at_age=101, emotional_weight=3.0,
        ))
        assert len(sset.memories) == MAX_MEMORIES
        assert all(m.event_id != "trivial" for m in sset.memories)
        assert any(m.event_id == "important" for m in sset.memories)


class TestGetRecent:
    def test_get_recent_returns_n_most_recent(self):
        sset = StoryMemorySet()
        for i in range(10):
            sset.add(StoryMemory(
                event_id=f"evt_{i}", summary=f"事件{i}",
                happened_at_age=10 + i,
            ))
        recent = sset.get_recent(3)
        assert len(recent) == 3
        # Most recent: ages 19, 18, 17
        assert [m.happened_at_age for m in recent] == [19, 18, 17]

    def test_get_recent_empty_set(self):
        sset = StoryMemorySet()
        assert sset.get_recent(5) == []

    def test_get_recent_less_than_n(self):
        sset = StoryMemorySet()
        sset.add(StoryMemory(event_id="evt_0", summary="唯一事件", happened_at_age=16))
        assert len(sset.get_recent(10)) == 1

    def test_get_recent_default_n(self):
        sset = StoryMemorySet()
        for i in range(10):
            sset.add(StoryMemory(
                event_id=f"evt_{i}", summary=f"事件{i}",
                happened_at_age=i,
            ))
        recent = sset.get_recent()
        assert len(recent) == 5
        assert [m.happened_at_age for m in recent] == [9, 8, 7, 6, 5]


class TestToPromptContext:
    def test_empty_set_returns_empty_string(self):
        sset = StoryMemorySet()
        assert sset.to_prompt_context() == ""

    def test_single_memory_format(self):
        sset = StoryMemorySet()
        sset.add(StoryMemory(event_id="evt_0", summary="拜入青云门", happened_at_age=16))
        ctx = sset.to_prompt_context()
        assert ctx == "【过往记忆】\n年龄16: 拜入青云门"

    def test_multiple_memories_format(self):
        sset = StoryMemorySet()
        sset.add(StoryMemory(event_id="evt_0", summary="拜入青云门", happened_at_age=16))
        sset.add(StoryMemory(event_id="evt_1", summary="获得筑基丹", happened_at_age=22))
        ctx = sset.to_prompt_context()
        lines = ctx.split("\n")
        assert lines[0] == "【过往记忆】"
        assert lines[1] == "年龄16: 拜入青云门"
        assert lines[2] == "年龄22: 获得筑基丹"

    def test_no_header_when_empty(self):
        sset = StoryMemorySet()
        ctx = sset.to_prompt_context()
        assert ctx == ""
        assert "【过往记忆】" not in ctx

    def test_preserves_insertion_order(self):
        sset = StoryMemorySet()
        sset.add(StoryMemory(event_id="a", summary="第一件", happened_at_age=10))
        sset.add(StoryMemory(event_id="b", summary="第二件", happened_at_age=20))
        sset.add(StoryMemory(event_id="c", summary="第三件", happened_at_age=15))
        ctx = sset.to_prompt_context()
        lines = ctx.split("\n")
        # Order preserved: 10, 20, 15 (insertion order)
        assert "年龄10" in lines[1]
        assert "年龄20" in lines[2]
        assert "年龄15" in lines[3]


class TestSerialization:
    def test_memory_serialization_roundtrip(self):
        m = StoryMemory(
            event_id="evt_001",
            summary="获得筑基丹",
            tags_involved=["pill", "fortune"],
            happened_at_age=22,
            emotional_weight=4.0,
        )
        data = m.model_dump()
        restored = StoryMemory.model_validate(data)
        assert restored.event_id == "evt_001"
        assert restored.emotional_weight == 4.0
        assert restored.tags_involved == ["pill", "fortune"]

    def test_memoryset_serialization_roundtrip(self):
        sset = StoryMemorySet()
        sset.add(StoryMemory(event_id="a", summary="事件A", happened_at_age=10))
        sset.add(StoryMemory(event_id="b", summary="事件B", happened_at_age=20))

        data = sset.model_dump()
        restored = StoryMemorySet.model_validate(data)
        assert len(restored.memories) == 2
        assert restored.memories[0].event_id == "a"
        assert restored.memories[1].event_id == "b"


class TestEdgeCases:
    def test_eviction_with_one_memory_over_capacity(self):
        sset = StoryMemorySet()
        for i in range(MAX_MEMORIES + 5):
            sset.add(StoryMemory(
                event_id=f"evt_{i}", summary=f"记忆{i}",
                happened_at_age=i, emotional_weight=float(i % 3 + 1),
            ))
        assert len(sset.memories) == MAX_MEMORIES

    def test_get_recent_with_n_zero(self):
        sset = StoryMemorySet()
        sset.add(StoryMemory(event_id="a", summary="单事件", happened_at_age=10))
        assert sset.get_recent(0) == []

    def test_multiple_evictions_preserves_highest_weight(self):
        sset = StoryMemorySet()
        # Add MAX_MEMORIES with low weight
        for i in range(MAX_MEMORIES):
            sset.add(StoryMemory(
                event_id=f"low_{i}", summary=f"低权重{i}",
                happened_at_age=i, emotional_weight=0.5,
            ))
        # Add 5 high-weight memories one by one
        for i in range(5):
            sset.add(StoryMemory(
                event_id=f"high_{i}", summary=f"高权重{i}",
                happened_at_age=100 + i, emotional_weight=4.0,
            ))
        assert len(sset.memories) == MAX_MEMORIES
        # All 5 high-weight should survive
        high_count = sum(1 for m in sset.memories if m.emotional_weight == 4.0)
        assert high_count == 5
        # Only 15 low-weight survive
        low_count = sum(1 for m in sset.memories if m.emotional_weight == 0.5)
        assert low_count == MAX_MEMORIES - 5
