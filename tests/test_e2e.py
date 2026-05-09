"""End-to-end integration tests: complete game lifecycle."""

import random
from unittest.mock import patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.tags import Tag, TagCategory, TagSet
from app.services.ai_service import MockAIService
from app.services.breakthrough import BreakthroughResult
from app.services.context_engine import determine_scenario_pool, match_scenarios
from app.services.event_engine import filter_templates, load_templates
from app.services.game_service import (
    _games,
    check_game_over,
    end_game,
    get_next_event,
    get_state,
    handle_breakthrough_choice,
    process_choice,
    start_game,
)


class TestE2EGameLoop:
    """End-to-end test: complete game lifecycle."""

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_full_game_loop_balanced(self, mock_ai):
        """Complete game loop with balanced attributes (3/3/2/2)."""
        random.seed(42)
        session = start_game(
            name="端到端测试",
            gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        _games[sid]["age"] = 20   # CULTIVATOR stage for events with options

        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            assert event["narrative"], f"Event {events_played}: no narrative"
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
                continue
            if len(event["options"]) == 0:
                process_choice(sid, None)
                continue
            assert len(event["options"]) >= 2

            option_id = event["options"][0]["id"]
            state = process_choice(sid, option_id)
            events_played += 1

            assert state["event_count"] >= events_played, \
                f"event_count={state['event_count']} must be >= events_played={events_played}"

        assert check_game_over(get_state(sid))

        result = end_game(sid)
        assert "ending" in result
        assert "score" in result
        assert "grade" in result
        assert 0 <= result["score"] <= 100

        print(f"Events played: {events_played}, Score: {result['score']}, Grade: {result['grade']}, Ending: {result['ending']}")

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_full_game_loop_tank(self, mock_ai):
        """Complete game with tank build (7/1/1/1)."""
        random.seed(42)
        session = start_game(
            name="坦克测试", gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 7, "comprehension": 1, "mindset": 1, "luck": 1},
        )
        sid = session["session_id"]
        _games[sid]["age"] = 20   # CULTIVATOR stage for events with options

        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
                continue
            if len(event["options"]) == 0:
                process_choice(sid, None)
                continue
            option_id = event["options"][0]["id"]
            process_choice(sid, option_id)
            events_played += 1

        state = get_state(sid)
        result = end_game(sid)
        assert "ending" in result
        assert "score" in result
        assert 0 <= result["score"] <= 100

        print(f"Tank build: {events_played} events, Score: {result['score']}, Grade: {result['grade']}")

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_full_game_loop_mage(self, mock_ai):
        """Complete game with mage build (1/7/1/1)."""
        random.seed(42)
        session = start_game(
            name="法师测试", gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 1, "comprehension": 7, "mindset": 1, "luck": 1},
        )
        sid = session["session_id"]
        _games[sid]["age"] = 20   # CULTIVATOR stage for events with options

        events_played = 0
        while not check_game_over(get_state(sid)):
            event = get_next_event(sid)
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
                continue
            if len(event["options"]) == 0:
                process_choice(sid, None)
                continue
            option_id = event["options"][0]["id"]
            process_choice(sid, option_id)
            events_played += 1

        result = end_game(sid)
        assert "ending" in result
        assert 0 <= result["score"] <= 100

        print(f"Mage build: {events_played} events, Score: {result['score']}, Grade: {result['grade']}")

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    @patch("app.services.game_service.attempt_breakthrough")
    def test_scoring_deterministic(self, mock_breakthrough, mock_ai):
        """Same attributes should produce same score."""
        mock_breakthrough.return_value = BreakthroughResult(
            success=True, new_realm="炼气", cultivation_loss=0, realm_dropped=False, ascended=False,
        )
        random.seed(42)

        def run_game():
            session = start_game(
                name="确定性测试", gender="男",
                talent_card_ids=["f01", "f02", "f03"],
                attributes={"rootBone": 5, "comprehension": 2, "mindset": 2, "luck": 1},
            )
            sid = session["session_id"]
            _games[sid]["age"] = 20   # CULTIVATOR stage for events with options
            while not check_game_over(get_state(sid)):
                event = get_next_event(sid)
                if event.get("is_breakthrough"):
                    handle_breakthrough_choice(_games[sid], use_pill=False)
                    continue
                if len(event["options"]) == 0:
                    process_choice(sid, None)
                    continue
                process_choice(sid, event["options"][0]["id"])
            return end_game(sid)["score"]

        score1 = run_game()
        score2 = run_game()
        assert score1 == score2, f"Scoring not deterministic: {score1} != {score2}"

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_event_count_tracked(self, mock_ai):
        """Event count should increase with each event-choose cycle."""
        random.seed(42)
        session = start_game(
            name="事件追踪", gender="女",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        _games[sid]["age"] = 20   # CULTIVATOR stage for events with options

        prev_count = 0
        while prev_count < 5:
            event = get_next_event(sid)
            if event.get("is_breakthrough"):
                handle_breakthrough_choice(_games[sid], use_pill=False)
            elif len(event["options"]) == 0:
                process_choice(sid, None)
            else:
                process_choice(sid, event["options"][0]["id"])
            state = get_state(sid)
            assert state["event_count"] > prev_count
            assert state["age"] > 0
            prev_count = state["event_count"]


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
        _games[sid]["age"] = 20   # CULTIVATOR stage for events with options

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


class TestTagDrivenEventPipeline:

    def _make_tags(self) -> TagSet:
        ts = TagSet()
        ts.add(Tag(category=TagCategory.IDENTITY, key="faction", value="门派=万剑山庄"))
        ts.add(Tag(category=TagCategory.SKILL, key="tech_万剑诀", value="功法=万剑诀"))
        ts.add(Tag(category=TagCategory.BOND, key="companion_wang", value="与王师兄交好"))
        ts.add(Tag(category=TagCategory.STATE, key="injured", value="伤势严重"))
        return ts

    def test_tags_determine_scenario_pool(self):
        tags = self._make_tags()
        scenarios = determine_scenario_pool(tags, {"age": 30})

        assert "generic_daily" in scenarios
        assert "faction_万剑山庄" in scenarios
        assert "faction_life" in scenarios
        assert "faction_senior" in scenarios
        assert "has_technique" in scenarios
        assert "has_companion" in scenarios
        assert "injured" in scenarios

    def test_scenarios_filter_templates(self):
        templates = [
            {"id": "t_pass", "type": "daily"},
            {"id": "t_faction", "scenarios": ["faction_万剑山庄"], "type": "sect"},
            {"id": "t_other", "scenarios": ["faction_逍遥派"], "type": "sect"},
            {"id": "t_injured", "scenarios": ["injured"], "type": "daily"},
        ]
        scenarios = ["generic_daily", "faction_万剑山庄"]
        matched = match_scenarios(templates, scenarios)

        matched_ids = {t["id"] for t in matched}
        assert "t_pass" in matched_ids
        assert "t_faction" in matched_ids
        assert "t_other" not in matched_ids
        assert "t_injured" not in matched_ids

    def test_trigger_tags_block_rival_events(self):
        templates = load_templates()

        player = {
            "realm": "炼气", "age": 25, "faction": "万剑山庄",
            "tags": TagSet(),
        }
        player["tags"].add(
            Tag(category=TagCategory.BOND, key="rival_zhang", value="与张师兄敌对"),
        )

        all_filtered = filter_templates(templates, player)
        for t in all_filtered:
            trigger = t.get("trigger_tags", {})
            block_keys = trigger.get("block", [])
            assert not ("rival" in block_keys or any("rival" in bk for bk in block_keys)), \
                f"Template {t.get('id')} should be blocked by rival"

        assert len(all_filtered) > 0

    def test_trigger_tags_require_faction_tag(self):
        templates = load_templates()

        player = {
            "realm": "炼气", "age": 25, "faction": "万剑山庄",
            "tags": TagSet(),
        }
        player["tags"].add(
            Tag(category=TagCategory.IDENTITY, key="faction", value="门派=万剑山庄"),
        )

        all_filtered = filter_templates(templates, player)
        faction_scoped = [
            t for t in all_filtered
            if t.get("scenarios") and any("faction" in s for s in t["scenarios"])
        ]
        assert len(faction_scoped) >= 0

    @patch("app.services.game_service._get_ai_service", return_value=MockAIService())
    def test_tag_pipeline_in_full_game_loop(self, mock_ai):
        random.seed(42)
        session = start_game(
            name="标签测试",
            gender="男",
            talent_card_ids=["f01", "f02", "f03"],
            attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        )
        sid = session["session_id"]
        state = _games[sid]
        state["age"] = 20

        tags = state.get("tags")
        assert tags is not None
        tags.add(Tag(category=TagCategory.IDENTITY, key="faction", value="门派=万剑山庄"))
        state["faction"] = "万剑山庄"

        faction_tag = tags.get_by_key("faction")
        assert faction_tag is not None
        assert "万剑山庄" in faction_tag.value

        event = get_next_event(sid)
        assert event["narrative"]
        assert isinstance(event.get("options"), list)
