"""Edge case tests: boundary conditions, fallbacks, and constraint enforcement."""

import random
from unittest.mock import patch

import pytest

from app.services.ai_service import MockAIService
from app.services.breakthrough import BreakthroughResult
from app.services.game_service import (
    _calc_cultivation_gain,
    _games,
    check_game_over,
    end_game,
    get_next_event,
    get_state,
    handle_breakthrough_choice,
    process_choice,
    start_game,
)
from app.services.life_stage import can_attempt_breakthrough


class TestEdgeCases:
    """10 edge-case / boundary-condition tests."""

    def test_all_zero_attrs_raises(self):
        """All-zero attrs sum to 0 -> ValueError."""
        with pytest.raises(ValueError, match="总和必须为10"):
            start_game(
                name="零蛋",
                gender="男",
                talent_card_ids=["f01", "f02", "f03"],
                attributes={"rootBone": 0, "comprehension": 0, "mindset": 0, "luck": 0},
            )

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_all_in_one_attr_succeeds(self, mock_ai):
        """All 10 points in a single attr is valid (sum == 10)."""
        random.seed(42)
        session = start_game(
            name="一根筋",
            gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 10, "comprehension": 0, "mindset": 0, "luck": 0},
        )
        assert session["attributes"]["rootBone"] == 10
        sid = session["session_id"]
        _games[sid]["age"] = 20
        for _ in range(3):
            event = get_next_event(sid)
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
                continue
            if len(event["options"]) == 0:
                process_choice(sid, None)
                continue
            process_choice(sid, event["options"][0]["id"])
        assert not check_game_over(get_state(sid))

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_lifespan_ending(self, mock_ai):
        """Game ends when age >= lifespan (mortal: 80/5 = 16 events)."""
        random.seed(42)
        session = start_game(
            name="短命鬼",
            gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        _games[sid]["age"] = 20
        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
                continue
            if len(event["options"]) == 0:
                process_choice(sid, None)
                continue
            process_choice(sid, event["options"][0]["id"])
            events_played += 1
        state = get_state(sid)
        assert state["age"] >= state["lifespan"] or state["event_count"] >= 60
        result = end_game(sid)
        assert result["ending"] in ("寿终正寝", "功德圆满")
        assert 0 <= result["score"] <= 100

    def test_initial_spirit_stones_zero(self):
        """spirit_stones starts at 0."""
        session = start_game(
            name="穷鬼",
            gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        assert session["spirit_stones"] == 0

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_spirit_stones_never_negative(self, mock_ai):
        """spirit_stones clamped >= 0 even with negative consequences."""
        random.seed(42)
        session = start_game(
            name="守财奴",
            gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        _games[sid]["age"] = 20
        for _ in range(10):
            event = get_next_event(sid)
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
                continue
            if len(event["options"]) == 0:
                process_choice(sid, None)
                continue
            process_choice(sid, event["options"][0]["id"])
            assert get_state(sid)["spirit_stones"] >= 0

    def test_mock_ai_service_fallback(self):
        """MockAIService provides deterministic fallback responses."""
        mock = MockAIService()
        result = mock.generate_event("test", {"realm": "凡人"})
        assert result["narrative"] == "你在山间修炼，灵气充裕，修为有所增长。"
        assert len(result["options"]) == 2
        assert result["options"][0]["id"] == "opt1"
        assert mock.call_count == 1

    def test_mock_ai_service_empty_response(self):
        """MockAIService returns empty narrative/options gracefully."""
        mock = MockAIService(response={"narrative": "", "options": []})
        result = mock.generate_event("test", {})
        assert result["narrative"] == ""
        assert result["options"] == []
        assert mock.call_count == 1

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_no_sect_gameplay(self, mock_ai):
        """Game runs without any sect/faction."""
        random.seed(42)
        session = start_game(
            name="散修",
            gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        _games[sid]["age"] = 20
        assert session["faction"] == ""
        for _ in range(10):
            event = get_next_event(sid)
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
                continue
            if len(event["options"]) == 0:
                process_choice(sid, None)
                continue
            process_choice(sid, event["options"][0]["id"])
            assert get_state(sid)["faction"] == ""

    @patch("app.services.game_service.attempt_breakthrough")
    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_realm_never_regresses(self, mock_ai, mock_breakthrough):
        """Realm never decreases during gameplay."""
        def _always_succeed(state, use_pill=False):
            return BreakthroughResult(
                success=True, new_realm=state.get("realm", "凡人"), cultivation_loss=0,
                realm_dropped=False, ascended=False,
            )
        mock_breakthrough.side_effect = _always_succeed
        random.seed(42)
        session = start_game(
            name="上进",
            gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        _games[sid]["age"] = 20
        seen = []
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
                continue
            if len(event["options"]) == 0:
                process_choice(sid, None)
                continue
            process_choice(sid, event["options"][0]["id"])
            seen.append(get_state(sid)["realm"])
        assert sorted(seen, reverse=True) == seen  # never regresses

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_mortal_realm_finishes(self, mock_ai):
        """Game started in mortal realm eventually finishes."""
        random.seed(42)
        session = start_game(
            name="凡人终章",
            gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        _games[sid]["age"] = 20
        assert session["realm"] == "凡人"
        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
                continue
            if len(event["options"]) == 0:
                process_choice(sid, None)
                continue
            process_choice(sid, event["options"][0]["id"])
            events_played += 1
        result = end_game(sid)
        assert "ending" in result
        assert "score" in result
        assert "grade" in result
        assert events_played > 0


# ============================================================================
# Age boundary tests (T12)
# ============================================================================


class TestAgeBoundaries:
    """Boundary tests for life-stage transitions and cultivation."""

    def test_age_3_cultivation_gain_zero(self):
        """age=3 (INFANT) → cultivation multiplier = 0."""
        # INFANT: multiplier = 0.0, so base * 0 = 0
        gain = _calc_cultivation_gain("daily", 5, [], 3)
        assert gain == 0.0

    def test_age_12_cultivation_gain_half(self):
        """age=12 (YOUTH) → cultivation multiplier = 0.5, total = base * comp * tech * stage."""
        # daily + comprehension=5 + no technique + YOUTH(0.5) = 10 * 1.5 * 0.5 * 0.5 = 3.75
        gain = _calc_cultivation_gain("daily", 5, [], 12)
        assert gain == 3.75

    def test_age_16_can_attempt_breakthrough(self):
        """age=16 (CULTIVATOR) → can_attempt_breakthrough = True."""
        assert can_attempt_breakthrough(16) is True

    def test_age_15_cannot_attempt_breakthrough(self):
        """age=15 (YOUTH) → can_attempt_breakthrough = False."""
        assert can_attempt_breakthrough(15) is False

    def test_age_0_cultivation_gain_zero(self):
        """age=0 (INFANT) → cultivation multiplier = 0."""
        gain = _calc_cultivation_gain("daily", 5, [], 0)
        assert gain == 0.0
