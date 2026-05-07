"""Tests for Pydantic v2 data models (Player, Event, Game schemas)."""

import pytest
from pydantic import ValidationError

from app.models.player import Attributes, PlayerState, Technique, InventoryItem, SectInfo
from app.models.event import EventResponse, EventOption, EventRequest, EventChooseRequest, ChooseResponse, AftermathResponse, BreakthroughInfo
from app.models.game import GameStartRequest, GameStartResponse, GameEndResponse, LeaderboardEntry


# ── Attributes ──────────────────────────────────────────────────────────────────

class TestAttributes:
    """root_bone/comprehension/mindset/luck: int 0-10, sum must be 10."""

    def test_valid_attributes(self):
        attrs = Attributes(root_bone=3, comprehension=3, mindset=2, luck=2)
        assert attrs.root_bone == 3
        assert attrs.comprehension == 3
        assert attrs.mindset == 2
        assert attrs.luck == 2

    def test_sum_too_high_raises(self):
        with pytest.raises(ValidationError):
            Attributes(root_bone=5, comprehension=5, mindset=5, luck=5)  # sum=20

    def test_sum_too_low_raises(self):
        with pytest.raises(ValidationError):
            Attributes(root_bone=1, comprehension=1, mindset=1, luck=1)  # sum=4

    def test_field_out_of_range_negative(self):
        with pytest.raises(ValidationError):
            Attributes(root_bone=-1, comprehension=3, mindset=4, luck=3)

    def test_field_out_of_range_over_10(self):
        with pytest.raises(ValidationError):
            Attributes(root_bone=11, comprehension=0, mindset=0, luck=-1)

    def test_all_ten_on_one_attribute(self):
        attrs = Attributes(root_bone=10, comprehension=0, mindset=0, luck=0)
        assert attrs.root_bone == 10
        assert attrs.luck == 0


# ── Technique / InventoryItem / SectInfo ───────────────────────────────────────

class TestTechnique:
    def test_valid_technique(self):
        t = Technique(id="sword_art", name="剑诀", description="基础剑法", modifier=1.2)
        assert t.id == "sword_art"
        assert t.modifier == 1.2

    def test_default_modifier(self):
        t = Technique(id="t2", name="无")
        assert t.modifier == 1.0


class TestInventoryItem:
    def test_valid_item(self):
        item = InventoryItem(id="herb_1", name="灵芝草", quantity=3)
        assert item.quantity == 3

    def test_default_quantity(self):
        item = InventoryItem(id="herb_1", name="灵芝草")
        assert item.quantity == 1


class TestSectInfo:
    def test_valid_sect(self):
        sect = SectInfo(faction="青云门", rank="外门弟子")
        assert sect.faction == "青云门"


# ── EventOption / EventResponse ────────────────────────────────────────────────

class TestEventOption:
    def test_valid_option(self):
        opt = EventOption(id="opt_1", text="上前行礼", consequence_preview="获得老者好感")
        assert opt.id == "opt_1"
        assert opt.consequence_preview == "获得老者好感"

    def test_minimal_option(self):
        opt = EventOption(id="opt_1", text="上前行礼")
        assert opt.consequence_preview is None


class TestEventResponse:
    """narrative: 20-500 chars, options: 2-3 items."""

    def test_valid_response(self):
        resp = EventResponse(
            narrative="你站在山门前，一位白须老者缓步走来，目光如炬。",
            options=[
                EventOption(id="opt_1", text="上前行礼"),
                EventOption(id="opt_2", text="转身离开"),
            ],
        )
        assert len(resp.narrative) >= 20
        assert 2 <= len(resp.options) <= 3

    def test_response_with_metadata(self):
        resp = EventResponse(
            narrative="你站在山门前，一位白须老者缓步走来，目光如炬。",
            options=[
                EventOption(id="opt_1", text="上前行礼"),
                EventOption(id="opt_2", text="转身离开"),
            ],
            metadata={"event_type": "encounter"},
        )
        assert resp.metadata == {"event_type": "encounter"}

    def test_narrative_too_short_raises(self):
        with pytest.raises(ValidationError):
            EventResponse(
                narrative="你好。",  # 3 chars
                options=[
                    EventOption(id="opt_1", text="上前行礼"),
                    EventOption(id="opt_2", text="转身离开"),
                ],
            )

    def test_narrative_too_long_raises(self):
        with pytest.raises(ValidationError):
            EventResponse(
                narrative="山。" * 300,  # 600 chars
                options=[
                    EventOption(id="opt_1", text="上前行礼"),
                    EventOption(id="opt_2", text="转身离开"),
                ],
            )

    def test_too_few_options_raises(self):
        with pytest.raises(ValidationError):
            EventResponse(
                narrative="你站在山门前，一位白须老者缓步走来。",
                options=[EventOption(id="opt_1", text="上前行礼")],  # only 1
            )

    def test_too_many_options_raises(self):
        with pytest.raises(ValidationError):
            EventResponse(
                narrative="你站在山门前，一位白须老者缓步走来。",
                options=[
                    EventOption(id="opt_1", text="上前行礼"),
                    EventOption(id="opt_2", text="转身离开"),
                    EventOption(id="opt_3", text="询问老者"),
                    EventOption(id="opt_4", text="拔剑相向"),  # 4 options
                ],
            )


class TestEventRequest:
    def test_valid_request(self):
        req = EventRequest(player_id="p1", current_realm="炼气", event_count=5)
        assert req.player_id == "p1"
        assert req.event_count == 5

    def test_defaults(self):
        req = EventRequest(player_id="p1")
        assert req.current_realm == ""
        assert req.event_count == 0


class TestEventChooseRequest:
    def test_valid_request(self):
        req = EventChooseRequest(player_id="p1", event_id="1", option_id="opt_1")
        assert req.player_id == "p1"
        assert req.option_id == "opt_1"


# ── GameStartRequest / GameStartResponse ───────────────────────────────────────

class TestGameStartRequest:
    """name, gender Literal["男","女"], talent_card_ids[3], attributes(sum=10)."""

    def test_valid_request(self):
        req = GameStartRequest(
            name="测试玩家",
            gender="男",
            talent_card_ids=["talent_1", "talent_2", "talent_3"],
            attributes=Attributes(root_bone=3, comprehension=3, mindset=2, luck=2),
        )
        assert req.name == "测试玩家"
        assert req.gender == "男"
        assert len(req.talent_card_ids) == 3

    def test_invalid_talent_card_count_too_few(self):
        with pytest.raises(ValidationError):
            GameStartRequest(
                name="测试玩家",
                gender="男",
                talent_card_ids=["talent_1", "talent_2"],  # only 2
                attributes=Attributes(root_bone=3, comprehension=3, mindset=2, luck=2),
            )

    def test_invalid_talent_card_count_too_many(self):
        with pytest.raises(ValidationError):
            GameStartRequest(
                name="测试玩家",
                gender="男",
                talent_card_ids=["talent_1", "talent_2", "talent_3", "talent_4"],  # 4
                attributes=Attributes(root_bone=3, comprehension=3, mindset=2, luck=2),
            )

    def test_invalid_gender_raises(self):
        with pytest.raises(ValidationError):
            GameStartRequest(
                name="测试玩家",
                gender="其他",
                talent_card_ids=["talent_1", "talent_2", "talent_3"],
                attributes=Attributes(root_bone=3, comprehension=3, mindset=2, luck=2),
            )

    def test_attributes_sum_still_enforced(self):
        with pytest.raises(ValidationError):
            GameStartRequest(
                name="测试玩家",
                gender="男",
                talent_card_ids=["talent_1", "talent_2", "talent_3"],
                attributes=Attributes(root_bone=5, comprehension=5, mindset=5, luck=5),
            )

    def test_serialization_roundtrip(self):
        req = GameStartRequest(
            name="测试玩家",
            gender="男",
            talent_card_ids=["t1", "t2", "t3"],
            attributes=Attributes(root_bone=3, comprehension=3, mindset=2, luck=2),
        )
        data = req.model_dump()
        restored = GameStartRequest.model_validate(data)
        assert restored.name == req.name
        assert restored.attributes.root_bone == 3


class TestGameStartResponse:
    def test_valid_response(self):
        state = PlayerState(id="s1", name="玩家")
        resp = GameStartResponse(session_id="abc-123", state=state)
        assert resp.session_id == "abc-123"
        assert resp.state.name == "玩家"

    def test_serialization_roundtrip(self):
        state = PlayerState(
            id="s1", name="玩家", gender="男", talent_ids=["t1"],
            root_bone=3, comprehension=3, mindset=2, luck=2,
        )
        resp = GameStartResponse(session_id="abc-123", state=state)
        data = resp.model_dump()
        restored = GameStartResponse.model_validate(data)
        assert restored.session_id == "abc-123"
        assert restored.state.root_bone == 3


class TestGameEndResponse:
    def test_valid_response(self):
        state = PlayerState(id="s1", name="玩家")
        resp = GameEndResponse(session_id="abc-123", final_state=state, reason="寿终正寝")
        assert resp.reason == "寿终正寝"

    def test_default_reason(self):
        state = PlayerState(id="s1", name="玩家")
        resp = GameEndResponse(session_id="abc-123", final_state=state)
        assert resp.reason == ""


class TestLeaderboardEntry:
    def test_valid_entry(self):
        entry = LeaderboardEntry(rank=1, player_name="玩家甲", score=1000, realm="筑基")
        assert entry.rank == 1
        assert entry.score == 1000

    def test_with_ending(self):
        entry = LeaderboardEntry(rank=2, player_name="玩家乙", score=500, realm="炼气", ending_id="飞升")
        assert entry.ending_id == "飞升"

    def test_default_ending(self):
        entry = LeaderboardEntry(rank=3, player_name="玩家丙", score=100, realm="凡人")
        assert entry.ending_id is None


# ── PlayerState Serialization ──────────────────────────────────────────────────

class TestPlayerState:
    """PlayerState: maps players table, supports JSON round-trip."""

    FULL_STATE_KWARGS = dict(
        id="test-id",
        name="测试玩家",
        gender="男",
        talent_ids=["talent_1", "talent_2"],
        root_bone=3,
        comprehension=4,
        mindset=2,
        luck=1,
        realm="炼气期",
        realm_progress=0.5,
        health=85.0,
        qi=12.0,
        lifespan=95,
        faction="青云门",
        spirit_stones=50,
        techniques=["sword_art"],
        inventory=["herb_1", "herb_2"],
        event_count=3,
        score=150,
        ending_id=None,
        is_alive=True,
        last_active_at="2026-05-04T10:00:00",
    )

    def test_valid_full_state(self):
        state = PlayerState(**self.FULL_STATE_KWARGS)
        for key, val in self.FULL_STATE_KWARGS.items():
            assert getattr(state, key) == val, f"Mismatch for {key}"

    def test_serialization_roundtrip(self):
        state = PlayerState(**self.FULL_STATE_KWARGS)
        data = state.model_dump()
        restored = PlayerState.model_validate(data)
        assert restored.id == state.id
        assert restored.name == state.name
        assert restored.is_alive is True
        assert restored.talent_ids == ["talent_1", "talent_2"]
        assert restored.techniques == ["sword_art"]
        assert restored.inventory == ["herb_1", "herb_2"]

    def test_minimal_state(self):
        """PlayerState only requires id and name; others get defaults."""
        state = PlayerState(id="new-id", name="新手")
        assert state.health == 100.0
        assert state.qi == 0.0
        assert state.lifespan == 100
        assert state.is_alive is True
        assert state.inventory == []
        assert state.techniques == []
        assert state.score == 0
        assert state.event_count == 0


# ── ChooseResponse / AftermathResponse / BreakthroughInfo ─────────────────────


class TestChooseResponse:
    def test_minimal(self):
        """ChooseResponse with only required fields."""
        resp = ChooseResponse(
            state={"age": 10},
            aftermath={"cultivation_change": 5.0, "age_advance": 1},
        )
        assert resp.aftermath.cultivation_change == 5.0
        assert resp.aftermath.narrative is None
        assert resp.aftermath.breakthrough is None

    def test_full(self):
        """ChooseResponse with all fields."""
        resp = ChooseResponse(
            state={"age": 10},
            aftermath={
                "cultivation_change": 5.0,
                "age_advance": 1,
                "narrative": "你选择了修炼。",
                "breakthrough": {
                    "message": "突破成功！",
                    "new_realm": "炼气",
                    "success": True,
                },
            },
        )
        assert resp.aftermath.narrative == "你选择了修炼。"
        assert resp.aftermath.breakthrough.message == "突破成功！"
        assert resp.aftermath.breakthrough.new_realm == "炼气"
        assert resp.aftermath.breakthrough.success is True

    def test_serialization_roundtrip(self):
        resp = ChooseResponse(
            state={"age": 10, "cultivation": 15.0},
            aftermath={
                "cultivation_change": 5.0,
                "age_advance": 1,
                "narrative": "你选择了修炼。",
            },
        )
        data = resp.model_dump()
        restored = ChooseResponse.model_validate(data)
        assert restored.aftermath.cultivation_change == 5.0
        assert restored.aftermath.age_advance == 1
        assert restored.aftermath.narrative == "你选择了修炼。"


class TestAftermathResponse:
    def test_defaults(self):
        resp = AftermathResponse()
        assert resp.cultivation_change == 0.0
        assert resp.age_advance == 0
        assert resp.narrative is None
        assert resp.breakthrough is None

    def test_with_breakthrough(self):
        resp = AftermathResponse(
            cultivation_change=5.0,
            age_advance=1,
            narrative="你选择了修炼。",
            breakthrough={"message": "突破成功！", "new_realm": "炼气", "success": True},
        )
        assert resp.breakthrough.message == "突破成功！"
        assert resp.breakthrough.new_realm == "炼气"


class TestBreakthroughInfo:
    def test_minimal(self):
        info = BreakthroughInfo(message="突破成功！")
        assert info.message == "突破成功！"
        assert info.new_realm is None
        assert info.success is None

    def test_full(self):
        info = BreakthroughInfo(message="突破成功！", new_realm="炼气", success=True)
        assert info.message == "突破成功！"
        assert info.new_realm == "炼气"
        assert info.success is True
