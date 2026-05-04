"""Tests for game state, end, and leaderboard endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.game_service import start_game


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _create_test_game():
    """Helper: 创建测试游戏"""
    return start_game(
        name="测试仙人", gender="男",
        talent_card_ids=["f01", "f02", "f03"],
        attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
    )


@pytest.mark.asyncio
async def test_get_state_success(client):
    game = _create_test_game()
    response = await client.get(f"/api/v1/game/state/{game['session_id']}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_state_not_found(client):
    response = await client.get("/api/v1/game/state/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_end_game_success(client):
    game = _create_test_game()
    response = await client.post("/api/v1/game/end", json={"session_id": game["session_id"]})
    assert response.status_code == 200
    data = response.json()
    assert "ending" in data
    assert "score" in data
    assert "grade" in data


@pytest.mark.asyncio
async def test_end_game_not_found(client):
    response = await client.post("/api/v1/game/end", json={"session_id": "nonexistent"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_leaderboard_returns_list(client):
    response = await client.get("/api/v1/game/leaderboard")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
