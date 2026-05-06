import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.game_service import start_game, _games


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _create_test_game():
    game = start_game(
        name="测试仙人", gender="男",
        talent_card_ids=["f01", "f02", "f03"],
        attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
    )
    _games[game["session_id"]]["age"] = 20   # CULTIVATOR stage for events with options
    return game


@pytest.mark.asyncio
async def test_get_event_success(client):
    game = _create_test_game()
    response = await client.post(
        "/api/v1/game/event",
        json={"player_id": game["session_id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "narrative" in data
    assert "options" in data
    assert isinstance(data["options"], list)
    assert len(data["options"]) >= 2


@pytest.mark.asyncio
async def test_get_event_game_over(client):
    game = _create_test_game()
    await client.post("/api/v1/game/end", json={"session_id": game["session_id"]})
    response = await client.post(
        "/api/v1/game/event",
        json={"player_id": game["session_id"]},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Game is already over"


@pytest.mark.asyncio
async def test_get_event_not_found(client):
    response = await client.post(
        "/api/v1/game/event",
        json={"player_id": "nonexistent"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_choose_success(client):
    game = _create_test_game()
    event_resp = await client.post(
        "/api/v1/game/event",
        json={"player_id": game["session_id"]},
    )
    assert event_resp.status_code == 200
    event_data = event_resp.json()

    option_id = event_data["options"][0]["id"]
    response = await client.post(
        "/api/v1/game/event/choose",
        json={"session_id": game["session_id"], "option_id": option_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert "state" in data
    assert "aftermath" in data
    assert data["aftermath"]["cultivation_change"] > 0
    assert data["aftermath"]["age_advance"] > 0


@pytest.mark.asyncio
async def test_choose_invalid_option(client):
    game = _create_test_game()
    await client.post(
        "/api/v1/game/event",
        json={"player_id": game["session_id"]},
    )
    response = await client.post(
        "/api/v1/game/event/choose",
        json={"session_id": game["session_id"], "option_id": "invalid_option"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_choose_no_current_event(client):
    game = _create_test_game()
    response = await client.post(
        "/api/v1/game/event/choose",
        json={"session_id": game["session_id"], "option_id": "opt_1"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_event_choose_loop(client):
    game = _create_test_game()
    for _ in range(3):
        event_resp = await client.post(
            "/api/v1/game/event",
            json={"player_id": game["session_id"]},
        )
        assert event_resp.status_code == 200
        event_data = event_resp.json()

        option_id = event_data["options"][0]["id"]
        choose_resp = await client.post(
            "/api/v1/game/event/choose",
            json={"session_id": game["session_id"], "option_id": option_id},
        )
        assert choose_resp.status_code == 200

    state_resp = await client.get(f"/api/v1/game/state/{game['session_id']}")
    assert state_resp.status_code == 200
    assert state_resp.json()["event_count"] == 3
