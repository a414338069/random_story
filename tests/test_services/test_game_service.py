"""Tests for game service (Task 11).

RED phase: All tests should fail initially.
"""

import random
from unittest.mock import patch

import pytest

from app.database import get_db
from app.services.breakthrough import BreakthroughResult
from app.services.game_service import (
    start_game,
    get_next_event,
    process_choice,
    get_state,
    end_game,
    check_game_over,
    handle_breakthrough_choice,
    _calc_cultivation_gain,
    _build_ai_prompt,
    _check_breakthrough_warning,
    _handle_cultivation_overflow,
    _games,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_TALENT_IDS = ["f01", "l02", "x03"]
VALID_ATTRIBUTES = {"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2}


def _make_player_attrs_dict(root_bone=3, comprehension=3, mindset=2, luck=2):
    """Build attributes dict with sum=10 by default."""
    return {"rootBone": root_bone, "comprehension": comprehension, "mindset": mindset, "luck": luck}


def _insert_current_event(session_id, event_type="daily", options=None):
    """Insert a mock current event into the game state for testing process_choice."""
    if options is None:
        options = [
            {"id": "opt1", "text": "继续修炼", "consequences": {}},
            {"id": "opt2", "text": "外出探索", "consequences": {"spirit_stones_gain": 50}},
        ]
    _games[session_id]["_current_event"] = {
        "id": "test_event_001",
        "type": event_type,
        "title": "测试事件",
        "options": options,
    }


# ---------------------------------------------------------------------------
# start_game()
# ---------------------------------------------------------------------------


class TestStartGame:
    def test_start_game_returns_valid_session(self):
        """start_game 返回 session_id + 初始状态."""
        random.seed(42)
        result = start_game("张三", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        assert "session_id" in result
        assert len(result["session_id"]) == 16  # uuid hex[:16]
        assert result["name"] == "张三"
        assert result["gender"] == "男"
        assert result["realm"] == "凡人"
        assert result["age"] == 0
        assert result["cultivation"] == 0
        assert result["spirit_stones"] == 0
        assert result["event_count"] == 0
        assert result["lifespan"] == 80
        assert result["faction"] == ""
        assert result["is_alive"] is True
        assert result["ascended"] is False
        assert result["talent_ids"] == VALID_TALENT_IDS
        assert result["techniques"] == []
        assert result["technique_grades"] == []

    def test_start_game_persisted_state(self):
        """start_game 后 get_state 可获取相同状态."""
        random.seed(42)
        result = start_game("李四", "女", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        state = get_state(sid)
        assert state["session_id"] == sid
        assert state["name"] == "李四"
        assert state["realm"] == "凡人"

    def test_start_game_invalid_talent_count(self):
        """天赋卡数量≠3 → ValueError."""
        with pytest.raises(ValueError, match="必须选择3张"):
            start_game("test", "男", ["f01", "l02"], _make_player_attrs_dict())

    def test_start_game_invalid_talent_id(self):
        """无效天赋卡ID → ValueError."""
        with pytest.raises(ValueError, match="无效的天赋卡ID"):
            start_game("test", "男", ["f01", "l02", "invalid_id"], _make_player_attrs_dict())

    def test_start_game_invalid_attributes_sum(self):
        """属性总和≠10 → ValueError."""
        with pytest.raises(ValueError, match="四维属性总和必须为10"):
            start_game("test", "男", VALID_TALENT_IDS, {"rootBone": 1, "comprehension": 1, "mindset": 1, "luck": 1})

    def test_start_game_invalid_attributes_range(self):
        """属性值超出 0-10 → ValueError."""
        with pytest.raises(ValueError, match="属性值必须在 0-10"):
            start_game("test", "男", VALID_TALENT_IDS, {"rootBone": 12, "comprehension": 0, "mindset": 0, "luck": -2})

    def test_start_game_invalid_gender(self):
        """无效性别 → ValueError."""
        with pytest.raises(ValueError, match="性别必须是"):
            start_game("test", "其他", VALID_TALENT_IDS, _make_player_attrs_dict())


# ---------------------------------------------------------------------------
# get_next_event()
# ---------------------------------------------------------------------------


class TestGetNextEvent:
    def test_get_next_event_returns_event(self):
        """get_next_event 返回有效事件 dict."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["age"] = 20   # CULTIVATOR stage for events with options
        event = get_next_event(sid)
        assert "event_id" in event
        assert "title" in event
        assert "narrative" in event
        assert "options" in event
        assert len(event["options"]) >= 1

    def test_get_next_event_stores_current_event(self):
        """get_next_event 把事件存储到 _current_event."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        get_next_event(sid)
        state = get_state(sid)
        assert "_current_event" in state
        assert state["_current_event"]["id"] is not None

    def test_get_next_event_bad_session(self):
        """无效 session_id → ValueError."""
        with pytest.raises(ValueError, match="session_id"):
            get_next_event("nonexistent")


# ---------------------------------------------------------------------------
# process_choice()
# ---------------------------------------------------------------------------


class TestProcessChoice:
    def test_process_choice_cultivation_increases(self):
        """选择后 cultivation 增加."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["age"] = 20  # CULTIVATOR stage for full multiplier
        _insert_current_event(sid, event_type="daily")
        old_cultivation = result["cultivation"]
        new_state = process_choice(sid, "opt1")
        assert new_state["cultivation"] > old_cultivation

    def test_process_choice_age_advances(self):
        """选择后 age 推进（凡人 time_span=1）."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _insert_current_event(sid, event_type="daily")
        new_state = process_choice(sid, "opt1")
        assert new_state["age"] == 1  # 凡人 time_span=1

    def test_process_choice_event_count_increments(self):
        """事件计数 +1."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _insert_current_event(sid, event_type="daily")
        new_state = process_choice(sid, "opt1")
        assert new_state["event_count"] == 1

    def test_process_choice_spirit_stones_gain(self):
        """选择带 spirit_stones_gain 的选项后灵石增加."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        # Bump to 练气 (spirit_stone_cap=1000) so gain is not capped away
        _games[sid]["realm"] = "练气"
        _games[sid]["lifespan"] = 120
        _insert_current_event(sid, event_type="adventure")
        new_state = process_choice(sid, "opt2")
        assert new_state["spirit_stones"] == 50

    def test_process_choice_spirit_stones_cap(self):
        """灵石超过上限被截断（凡人 spirit_stone_cap=50）."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["spirit_stones"] = 45  # near cap to test truncation
        _insert_current_event(sid, event_type="adventure")
        new_state = process_choice(sid, "opt2")
        # opt2 gives 50, 45+50=95, capped to 50
        assert new_state["spirit_stones"] == 50

    def test_process_choice_no_current_event(self):
        """没有当前事件时 process_choice → ValueError."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        with pytest.raises(ValueError, match="当前事件"):
            process_choice(result["session_id"], "opt1")

    def test_process_choice_invalid_option(self):
        """无效 option_id → ValueError."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _insert_current_event(sid, event_type="daily")
        with pytest.raises(ValueError, match="无效的选项"):
            process_choice(sid, "nonexistent")

    def test_process_choice_bad_session(self):
        """无效 session_id → ValueError."""
        with pytest.raises(ValueError, match="session_id"):
            process_choice("nonexistent", "opt1")


# ---------------------------------------------------------------------------
# _calc_cultivation_gain() — cultivation formula
# ---------------------------------------------------------------------------


class TestCultivationFormula:
    def test_daily_no_technique_comprehension_5(self):
        """daily + comprehension=5 + 无功法 → 10 * 1.5 * 0.5 = 7.5."""
        gain = _calc_cultivation_gain("daily", 5, [], 20)
        assert gain == 7.5

    def test_daily_no_technique_comprehension_0(self):
        """daily + comprehension=0 + 无功法 → 10 * 1.0 * 0.5 = 5.0."""
        gain = _calc_cultivation_gain("daily", 0, [], 20)
        assert gain == 5.0

    def test_daily_lingpin_technique(self):
        """daily + comprehension=5 + 灵品 → 10 * 1.5 * 1.5 = 22.5."""
        gain = _calc_cultivation_gain("daily", 5, ["灵品"], 20)
        assert gain == 22.5

    def test_adventure_no_technique(self):
        """adventure + comprehension=3 + 无功法 → 30 * 1.3 * 0.5 = 19.5."""
        gain = _calc_cultivation_gain("adventure", 3, [], 20)
        assert gain == 19.5

    def test_bottleneck_no_technique(self):
        """bottleneck + comprehension=2 + 无功法 → 5 * 1.2 * 0.5 = 3.0."""
        gain = _calc_cultivation_gain("bottleneck", 2, [], 20)
        assert gain == 3.0

    def test_multiple_techniques_average(self):
        """多个功法取平均: 凡品(1.0) + 仙品(3.0) = avg 2.0."""
        gain = _calc_cultivation_gain("daily", 5, ["凡品", "仙品"], 20)
        # 10 * 1.5 * 2.0 = 30.0
        assert gain == 30.0

    def test_xuanpin_technique(self):
        """玄品功法 modifier = 2.0."""
        gain = _calc_cultivation_gain("daily", 5, ["玄品"], 20)
        # 10 * 1.5 * 2.0 = 30.0
        assert gain == 30.0

    def test_xianpin_technique(self):
        """仙品功法 modifier = 3.0."""
        gain = _calc_cultivation_gain("daily", 5, ["仙品"], 20)
        # 10 * 1.5 * 3.0 = 45.0
        assert gain == 45.0

    def test_unknown_grade_defaults(self):
        """未知功法品级默认 modifier = 0.5."""
        gain = _calc_cultivation_gain("daily", 5, ["未知品"], 20)
        # 10 * 1.5 * 0.5 = 7.5
        assert gain == 7.5

    def test_unknown_event_type_defaults(self):
        """未知事件类型默认 base=10."""
        gain = _calc_cultivation_gain("unknown_type", 5, [], 20)
        # 10 * 1.5 * 0.5 = 7.5
        assert gain == 7.5

    def test_understanding_higher_cultivation(self):
        """comprehension=10 vs 0: comp=10 gives (1+1.0)/(1+0.0)=2x gain."""
        g10 = _calc_cultivation_gain("daily", 10, [], 20)
        g0 = _calc_cultivation_gain("daily", 0, [], 20)
        # g10 = 10 * 2.0 * 0.5 = 10.0
        # g0 = 10 * 1.0 * 0.5 = 5.0
        assert g10 == 2 * g0


# ---------------------------------------------------------------------------
# Cultivation overflow (修为溢出 → realm_progress)
# ---------------------------------------------------------------------------


class TestCultivationOverflow:
    def test_cultivation_overflow_sets_pending_breakthrough(self):
        """修为超过 cultivation_req → cap at next_req-1，设置 _pending_breakthrough."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["age"] = 20  # CULTIVATOR stage for full cultivation multiplier + allow breakthrough
        _insert_current_event(sid, event_type="adventure")
        # Set cultivation near cap manually
        _games[sid]["cultivation"] = 95  # 凡人 cultivation_req = 100
        new_state = process_choice(sid, "opt1")
        # adventure + comprehension=3 + no technique = 30 * 1.3 * 0.5 = 19.5
        # 95 + 19.5 = 114.5 >= 100 → cap at 99, set _pending_breakthrough
        assert new_state["_pending_breakthrough"] is True
        assert new_state["cultivation"] == pytest.approx(99.0, abs=0.01)
        assert new_state["realm_progress"] == pytest.approx(0.99, abs=0.001)
        assert new_state["realm"] == "凡人"  # realm should NOT change

    def test_no_overflow_when_below_req(self):
        """正常修炼不溢出."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["age"] = 20  # CULTIVATOR stage for full cultivation multiplier
        _insert_current_event(sid, event_type="daily")
        _games[sid]["cultivation"] = 10
        new_state = process_choice(sid, "opt1")
        # daily + comprehension=3 + no technique = 10 * 1.3 * 0.5 = 6.5
        # 10 + 6.5 = 16.5 < 100, no overflow
        assert new_state["cultivation"] == pytest.approx(16.5)
        assert new_state["realm_progress"] == 0.0
        assert "_pending_breakthrough" not in new_state


# ---------------------------------------------------------------------------
# check_game_over()
# ---------------------------------------------------------------------------


class TestCheckGameOver:
    def test_check_game_over_age(self):
        """年龄 ≥ 寿命 → True."""
        state = {"age": 80, "lifespan": 80, "event_count": 10, "ascended": False}
        assert check_game_over(state) is True

    def test_check_game_over_events(self):
        """事件数 ≥ 60 → True."""
        state = {"age": 30, "lifespan": 80, "event_count": 60, "ascended": False}
        assert check_game_over(state) is True

    def test_check_game_over_ascended(self):
        """ascended=True → True."""
        state = {"age": 100, "lifespan": 20000, "event_count": 10, "ascended": True}
        assert check_game_over(state) is True

    def test_check_game_not_over(self):
        """正常状态 → False."""
        state = {"age": 30, "lifespan": 80, "event_count": 10, "ascended": False}
        assert check_game_over(state) is False

    def test_check_game_over_age_over_lifespan(self):
        """age > lifespan → True."""
        state = {"age": 85, "lifespan": 80, "event_count": 5, "ascended": False}
        assert check_game_over(state) is True


# ---------------------------------------------------------------------------
# end_game()
# ---------------------------------------------------------------------------


class TestEndGame:
    def test_end_game_returns_ending(self):
        """end_game 返回 ending + score + grade."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _insert_current_event(sid, event_type="daily")
        process_choice(sid, "opt1")
        end_result = end_game(sid)
        assert "ending" in end_result
        assert "score" in end_result
        assert "grade" in end_result
        assert "session_id" in end_result

    def test_end_game_deterministic(self):
        """同一状态两次结算 → 相同分数."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _insert_current_event(sid, event_type="daily")
        process_choice(sid, "opt1")
        r1 = end_game(sid)
        # Re-set is_alive to True to allow ending again
        _games[sid]["is_alive"] = True
        r2 = end_game(sid)
        assert r1["score"] == r2["score"]
        assert r1["ending"] == r2["ending"]
        assert r1["grade"] == r2["grade"]

    def test_end_game_ascended_feisheng(self):
        """飞升玩家 end_game → 飞升成仙."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["ascended"] = True
        _games[sid]["realm"] = "渡劫飞升"
        _games[sid]["lifespan"] = 20000
        _games[sid]["age"] = 20000
        end_result = end_game(sid)
        assert end_result["ending"] == "飞升成仙"

    def test_end_game_bad_session(self):
        """无效 session_id → ValueError."""
        with pytest.raises(ValueError, match="session_id"):
            end_game("nonexistent")


# ---------------------------------------------------------------------------
# get_state()
# ---------------------------------------------------------------------------


class TestGetState:
    def test_get_state_nonexistent(self):
        """无效 session_id → ValueError."""
        with pytest.raises(ValueError, match="session_id"):
            get_state("nonexistent")


# ---------------------------------------------------------------------------
# Integration: full game lifecycle
# ---------------------------------------------------------------------------


class TestGameLifecycle:
    def test_full_lifecycle(self):
        """完整游戏流程: start → get_event → process → end."""
        random.seed(42)
        result = start_game("王五", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]

        # Run 3 events (skip narrative_only/quiet_year events with no options)
        events_processed = 0
        attempts = 0
        while events_processed < 3 and attempts < 10:
            attempts += 1
            event = get_next_event(sid)
            assert "options" in event
            if len(event["options"]) == 0:
                # narrative_only event (e.g. quiet_year) — auto-advance
                state = process_choice(sid, None)
                continue
            option_id = event["options"][0]["id"]
            state = process_choice(sid, option_id)
            assert state["event_count"] >= 1
            events_processed += 1

        # End the game
        end_result = end_game(sid)
        assert "ending" in end_result
        assert "score" in end_result
        assert "grade" in end_result

    def test_multiple_sessions_independent(self):
        """多个会话状态隔离."""
        random.seed(42)
        r1 = start_game("玩家A", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        r2 = start_game("玩家B", "女", VALID_TALENT_IDS, _make_player_attrs_dict())
        assert r1["session_id"] != r2["session_id"]
        assert r1["name"] == "玩家A"
        assert r2["name"] == "玩家B"

        # Modify player A state
        _insert_current_event(r1["session_id"], event_type="daily")
        process_choice(r1["session_id"], "opt1")

        # Player B should be unaffected
        state_b = get_state(r2["session_id"])
        assert state_b["age"] == 0
        assert state_b["event_count"] == 0
        assert state_b["cultivation"] == 0


# ---------------------------------------------------------------------------
# _build_ai_prompt() — AI prompt enrichment
# ---------------------------------------------------------------------------


class TestBuildAIPrompt:
    def test_build_ai_prompt_includes_recent_events(self):
        """Prompt should contain 【近期经历】 when recent_summaries provided."""
        event_ctx = {
            "player": {"realm": "凡人", "age": 10},
            "event_type": "daily",
            "title": "修炼",
            "prompt": "test prompt",
        }
        state = {"attributes": {"rootBone": 5, "comprehension": 5, "mindset": 5, "luck": 5}, "faction": "无"}
        summaries = [
            {"event_type": "daily", "narrative": "你在山中修炼", "chosen_option_id": "opt1", "consequences": {}},
            {"event_type": "adventure", "narrative": "你遇到了一只妖兽", "chosen_option_id": "opt2", "consequences": {}},
        ]
        prompt = _build_ai_prompt(event_ctx, state, recent_summaries=summaries)
        assert "近期经历" in prompt
        assert "你在山中修炼" in prompt

    def test_build_ai_prompt_includes_last_outcome(self):
        """Prompt should contain 【上一轮结果】 when last_outcome provided."""
        event_ctx = {
            "player": {"realm": "凡人", "age": 10},
            "event_type": "daily",
            "title": "修炼",
            "prompt": "test prompt",
        }
        state = {"attributes": {"rootBone": 5, "comprehension": 5, "mindset": 5, "luck": 5}, "faction": "无"}
        outcome = {"chosen_text": "继续修炼", "cultivation_change": 5.0, "age_advance": 1}
        prompt = _build_ai_prompt(event_ctx, state, last_outcome=outcome)
        assert "上一轮结果" in prompt
        assert "继续修炼" in prompt
        assert "+5.0" in prompt

    def test_build_ai_prompt_no_optional_sections(self):
        """Prompt should NOT contain optional sections when no data provided."""
        event_ctx = {
            "player": {"realm": "凡人", "age": 10},
            "event_type": "daily",
            "title": "修炼",
            "prompt": "test prompt",
        }
        state = {"attributes": {"rootBone": 5, "comprehension": 5, "mindset": 5, "luck": 5}, "faction": "无"}
        prompt = _build_ai_prompt(event_ctx, state)
        assert "近期经历" not in prompt
        assert "上一轮结果" not in prompt
        assert "当前境界" in prompt


class TestGetNextEventCaching:
    def test_get_next_event_caches_narrative(self):
        """get_next_event should cache narrative in state for process_choice."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        session_id = result["session_id"]

        event = get_next_event(session_id)
        state = get_state(session_id)

        assert "_current_narrative" in state
        assert state["_current_narrative"] == event["narrative"]


# ---------------------------------------------------------------------------
# _check_breakthrough_warning() — breakthrough proximity warning
# ---------------------------------------------------------------------------


class TestBreakthroughWarning:
    def test_warning_at_80_percent(self):
        """Warning triggers when cultivation >= 80% of next realm requirement."""
        state = {
            "realm": "凡人",
            "cultivation": 80.0,  # 练气 requires 100, 80/100 = 80%
        }
        result = _check_breakthrough_warning(state)
        assert result is not None
        assert "message" in result
        assert "80" in result["message"] or "突破" in result["message"]
        assert result["threshold"] == 80.0  # 100 * 0.8

    def test_no_warning_below_80_percent(self):
        """No warning when cultivation < 80% of next realm requirement."""
        state = {
            "realm": "凡人",
            "cultivation": 79.0,  # 79/100 = 79%
        }
        result = _check_breakthrough_warning(state)
        assert result is None

    def test_no_warning_at_max_realm(self):
        """No warning at maximum realm (渡劫飞升 has no next realm)."""
        state = {
            "realm": "渡劫飞升",
            "cultivation": 9999.0,
        }
        result = _check_breakthrough_warning(state)
        assert result is None

    def test_warning_above_threshold(self):
        """Warning still triggers above 80%."""
        state = {
            "realm": "凡人",
            "cultivation": 95.0,  # 95/100 = 95%
        }
        result = _check_breakthrough_warning(state)
        assert result is not None
        assert result["current"] == 95.0


# ---------------------------------------------------------------------------
# process_choice() — narrative, outcome, aftermath
# ---------------------------------------------------------------------------


class TestProcessChoiceNarrative:
    def test_full_narrative_saved_to_event_log(self):
        """process_choice should save full narrative text to event_log, not just title."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        session_id = result["session_id"]

        _insert_current_event(session_id, event_type="daily")

        state = get_state(session_id)
        state["_current_narrative"] = "这是一段详细的叙事文本，描述了你在山中的修炼经历。"

        process_choice(session_id, "opt1")

        conn = get_db()
        try:
            import sqlite3
            cursor = conn.execute(
                "SELECT narrative FROM event_logs WHERE player_id = ? ORDER BY event_index DESC LIMIT 1",
                (session_id,),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "这是一段详细的叙事文本，描述了你在山中的修炼经历。"
        finally:
            conn.close()

    def test_last_choice_outcome_constructed(self):
        """process_choice should construct _last_choice_outcome for AI context."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        session_id = result["session_id"]

        _insert_current_event(session_id, event_type="daily")
        process_choice(session_id, "opt1")

        state = get_state(session_id)

        assert "_last_choice_outcome" in state
        outcome = state["_last_choice_outcome"]
        assert "chosen_text" in outcome
        assert outcome["chosen_text"] == "继续修炼"
        assert "cultivation_change" in outcome
        assert "age_advance" in outcome

    def test_consequence_narrative_in_response(self):
        """process_choice should return aftermath with consequence narrative."""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        session_id = result["session_id"]

        _insert_current_event(session_id, event_type="daily")
        choice_result = process_choice(session_id, "opt1")

        assert "aftermath" in choice_result
        assert "narrative" in choice_result["aftermath"]
        assert choice_result["aftermath"]["narrative"]
        assert "继续修炼" in choice_result["aftermath"]["narrative"]
        assert "修为" in choice_result["aftermath"]["narrative"]


# ============================================================================
# T4: get_next_event returns breakthrough event when pending
# ============================================================================


class TestGetNextEventBreakthrough:
    def test_get_next_event_returns_breakthrough_event_when_pending(self):
        """当 _pending_breakthrough=True 时，get_next_event 返回突破事件"""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["_pending_breakthrough"] = True
        _games[sid]["age"] = 20

        event = get_next_event(sid)
        assert event["event_id"] == "breakthrough_pending"
        assert event["title"] == "境界突破"
        assert event["is_breakthrough"] is True
        assert event["has_options"] is True
        assert len(event["options"]) == 2
        assert event["options"][0]["id"] == "use_pill"
        assert event["options"][1]["id"] == "direct"

    def test_get_next_event_bypasses_ai_when_breakthrough_pending(self):
        """突破事件不调用 AI"""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["_pending_breakthrough"] = True
        _games[sid]["age"] = 20

        with patch("app.services.game_service._get_ai_service") as mock_ai:
            event = get_next_event(sid)
            mock_ai.assert_not_called()


# ============================================================================
# T4: handle_breakthrough_choice()
# ============================================================================


class TestHandleBreakthroughChoice:
    def test_handle_breakthrough_choice_success(self):
        """突破成功 → realm 提升 + cultivation 重置"""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["age"] = 20
        _games[sid]["cultivation"] = 99
        _games[sid]["_pending_breakthrough"] = True
        _games[sid]["_breakthrough_next_req"] = 100
        _games[sid]["_breakthrough_cultivation"] = 115

        random.seed(1)  # success seed
        outcome = handle_breakthrough_choice(_games[sid], use_pill=False)

        assert outcome["success"] is True
        assert outcome["new_realm"] == "练气"
        assert outcome["cultivation_loss"] == 0.0
        assert outcome["realm_dropped"] is False
        assert outcome["ascended"] is False
        assert "_pending_breakthrough" not in _games[sid]
        assert _games[sid]["realm"] == "练气"
        assert _games[sid]["cultivation"] == pytest.approx(15.0, abs=0.01)  # 115-100 overflow

    def test_handle_breakthrough_choice_failure(self):
        """突破失败 → cultivation 损失"""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["age"] = 20
        _games[sid]["cultivation"] = 99
        _games[sid]["_pending_breakthrough"] = True
        _games[sid]["_breakthrough_next_req"] = 100
        _games[sid]["_breakthrough_cultivation"] = 115

        random.seed(2)  # failure seed
        outcome = handle_breakthrough_choice(_games[sid], use_pill=False)

        assert outcome["success"] is False
        assert outcome["cultivation_loss"] > 0
        assert "_pending_breakthrough" not in _games[sid]
        assert _games[sid]["cultivation"] < 99  # loss applied

    def test_handle_breakthrough_choice_with_pill(self):
        """use_pill=True → 传递给 attempt_breakthrough → +15% 成功率"""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["age"] = 20
        _games[sid]["cultivation"] = 99
        _games[sid]["_pending_breakthrough"] = True
        _games[sid]["_breakthrough_next_req"] = 100
        _games[sid]["_breakthrough_cultivation"] = 115

        # Verify use_pill is passed through — we can't easily test the rate change
        # without mocking, but we verify the outcome dict has correct structure
        random.seed(1)
        outcome = handle_breakthrough_choice(_games[sid], use_pill=True)
        assert "success" in outcome
        assert "new_realm" in outcome
        assert "cultivation_loss" in outcome
        assert "realm_dropped" in outcome
        assert "ascended" in outcome
        assert "_pending_breakthrough" not in _games[sid]

    def test_handle_breakthrough_choice_clears_flag_on_both_outcomes(self):
        """无论成功失败，_pending_breakthrough 都会被清除"""
        random.seed(42)
        result = start_game("测试", "男", VALID_TALENT_IDS, _make_player_attrs_dict())
        sid = result["session_id"]
        _games[sid]["age"] = 20
        _games[sid]["cultivation"] = 99
        _games[sid]["_pending_breakthrough"] = True

        random.seed(1)
        handle_breakthrough_choice(_games[sid], use_pill=False)
        assert "_pending_breakthrough" not in _games[sid]

        # Try again with failure seed
        _games[sid]["_pending_breakthrough"] = True
        random.seed(2)
        handle_breakthrough_choice(_games[sid], use_pill=False)
        assert "_pending_breakthrough" not in _games[sid]

