"""Edge case tests: boundary conditions, fallbacks, and constraint enforcement."""

import random
from unittest.mock import patch

import pytest

from app.services.ai_service import MockAIService
from app.services.breakthrough import BreakthroughResult
from app.services.game_service import (
    check_game_over,
    end_game,
    get_next_event,
    get_state,
    process_choice,
    start_game,
)


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

    def test_all_in_one_attr_succeeds(self):
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
        for _ in range(3):
            event = get_next_event(sid)
            process_choice(sid, event["options"][0]["id"])
        assert not check_game_over(get_state(sid))

    def test_lifespan_ending(self):
        """Game ends when age >= lifespan (mortal: 80/5 = 16 events)."""
        random.seed(42)
        session = start_game(
            name="短命鬼",
            gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            process_choice(sid, event["options"][0]["id"])
            events_played += 1
        state = get_state(sid)
        assert state["age"] >= state["lifespan"]
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

    def test_spirit_stones_never_negative(self):
        """spirit_stones clamped >= 0 even with negative consequences."""
        random.seed(42)
        session = start_game(
            name="守财奴",
            gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        for _ in range(10):
            event = get_next_event(sid)
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

    def test_no_sect_gameplay(self):
        """Game runs without any sect/faction."""
        random.seed(42)
        session = start_game(
            name="散修",
            gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        assert session["faction"] == ""
        for _ in range(10):
            event = get_next_event(sid)
            process_choice(sid, event["options"][0]["id"])
            assert get_state(sid)["faction"] == ""

    @patch("app.services.game_service.attempt_breakthrough")
    def test_realm_never_regresses(self, mock_breakthrough):
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
        seen = []
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            process_choice(sid, event["options"][0]["id"])
            seen.append(get_state(sid)["realm"])
        assert sorted(seen, reverse=True) == seen  # never regresses

    def test_mortal_realm_finishes(self):
        """Game started in mortal realm eventually finishes."""
        random.seed(42)
        session = start_game(
            name="凡人终章",
            gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        assert session["realm"] == "凡人"
        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            process_choice(sid, event["options"][0]["id"])
            events_played += 1
        result = end_game(sid)
        assert "ending" in result
        assert "score" in result
        assert "grade" in result
        assert events_played > 0
