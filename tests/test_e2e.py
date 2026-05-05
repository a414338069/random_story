"""End-to-end integration tests: complete game lifecycle."""

import random
from unittest.mock import patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.breakthrough import BreakthroughResult
from app.services.game_service import (
    check_game_over,
    end_game,
    get_next_event,
    get_state,
    process_choice,
    start_game,
)


class TestE2EGameLoop:
    """End-to-end test: complete game lifecycle."""

    def test_full_game_loop_balanced(self):
        """Complete game loop with balanced attributes (3/3/2/2)."""
        random.seed(42)
        session = start_game(
            name="端到端测试",
            gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]

        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            assert event["narrative"], f"Event {events_played}: no narrative"
            assert len(event["options"]) >= 2

            option_id = event["options"][0]["id"]
            state = process_choice(sid, option_id)
            events_played += 1

            assert state["event_count"] == events_played

        assert check_game_over(get_state(sid))

        result = end_game(sid)
        assert "ending" in result
        assert "score" in result
        assert "grade" in result
        assert 0 <= result["score"] <= 100

        print(f"Events played: {events_played}, Score: {result['score']}, Grade: {result['grade']}, Ending: {result['ending']}")

    def test_full_game_loop_tank(self):
        """Complete game with tank build (7/1/1/1)."""
        random.seed(42)
        session = start_game(
            name="坦克测试", gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 7, "comprehension": 1, "mindset": 1, "luck": 1},
        )
        sid = session["session_id"]

        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            option_id = event["options"][0]["id"]
            process_choice(sid, option_id)
            events_played += 1

        state = get_state(sid)
        result = end_game(sid)
        assert "ending" in result
        assert "score" in result
        assert 0 <= result["score"] <= 100

        print(f"Tank build: {events_played} events, Score: {result['score']}, Grade: {result['grade']}")

    def test_full_game_loop_mage(self):
        """Complete game with mage build (1/7/1/1)."""
        random.seed(42)
        session = start_game(
            name="法师测试", gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 1, "comprehension": 7, "mindset": 1, "luck": 1},
        )
        sid = session["session_id"]

        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            option_id = event["options"][0]["id"]
            process_choice(sid, option_id)
            events_played += 1

        result = end_game(sid)
        assert "ending" in result
        assert 0 <= result["score"] <= 100

        print(f"Mage build: {events_played} events, Score: {result['score']}, Grade: {result['grade']}")

    @patch("app.services.game_service._get_ai_service")
    @patch("app.services.game_service.attempt_breakthrough")
    def test_scoring_deterministic(self, mock_breakthrough, mock_ai):
        """Same attributes should produce same score."""
        mock_breakthrough.return_value = BreakthroughResult(
            success=True, new_realm="练气", cultivation_loss=0, realm_dropped=False, ascended=False,
        )
        mock_ai.side_effect = Exception("AI disabled for deterministic test")
        random.seed(42)

        def run_game():
            session = start_game(
                name="确定性测试", gender="男",
                talent_card_ids=["f01", "f02", "f03"],
                attributes={"rootBone": 5, "comprehension": 2, "mindset": 2, "luck": 1},
            )
            sid = session["session_id"]
            while not check_game_over(get_state(sid)):
                event = get_next_event(sid)
                process_choice(sid, event["options"][0]["id"])
            return end_game(sid)["score"]

        score1 = run_game()
        score2 = run_game()
        assert score1 == score2, f"Scoring not deterministic: {score1} != {score2}"

    def test_event_count_tracked(self):
        """Event count should increase with each event-choose cycle."""
        random.seed(42)
        session = start_game(
            name="事件追踪", gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]

        for i in range(5):
            event = get_next_event(sid)
            process_choice(sid, event["options"][0]["id"])
            state = get_state(sid)
            assert state["event_count"] == i + 1
            assert state["age"] > 0


@pytest.mark.asyncio
async def test_all_api_endpoints_e2e():
    """Test all 6 API endpoints work together."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/api/v1/game/start", json={
            "name": "API测试", "gender": "男",
            "talent_card_ids": ["f01", "f02", "f03"],
            "attributes": {"root_bone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        })
        assert resp.status_code == 201
        data = resp.json()
        sid = data["session_id"]

        resp = await c.get(f"/api/v1/game/state/{sid}")
        assert resp.status_code == 200
        state = resp.json()
        assert state["realm"] == "凡人"

        resp = await c.post("/api/v1/game/event", json={"player_id": sid})
        assert resp.status_code == 200
        event_data = resp.json()
        assert "narrative" in event_data
        assert "options" in event_data

        option_id = event_data["options"][0]["id"]
        resp = await c.post("/api/v1/game/event/choose", json={
            "session_id": sid,
            "option_id": option_id,
        })
        assert resp.status_code == 200

        resp = await c.post("/api/v1/game/end", json={"session_id": sid})
        assert resp.status_code == 200
        result = resp.json()
        assert "score" in result

        resp = await c.get("/api/v1/game/leaderboard")
        assert resp.status_code == 200
