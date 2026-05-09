"""Tests for POST /api/v1/game/start"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestCreateGame:
    """Create game endpoint tests."""

    @pytest.mark.asyncio
    async def test_create_game_success(self, client):
        """正常请求 → 201 + sessionId + 完整初始状态"""
        response = await client.post(
            "/api/v1/game/start",
            json={
                "name": "测试玩家",
                "gender": "男",
                "talent_card_ids": ["f01", "l02", "x03"],
                "attributes": {
                    "root_bone": 3,
                    "comprehension": 3,
                    "mindset": 2,
                    "luck": 2,
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "state" in data
        state = data["state"]
        assert state["name"] == "测试玩家"
        assert state["gender"] == "男"
        assert state["realm"] == "凡人"
        assert state["root_bone"] == 6
        assert state["comprehension"] == 8
        assert state["mindset"] == 4
        assert state["luck"] == 4
        assert state["is_alive"] is True
        assert state["lifespan"] == 80
        assert state["spirit_stones"] == 0
        assert state["talent_ids"] == ["f01", "l02", "x03"]

    @pytest.mark.asyncio
    async def test_invalid_attributes_sum(self, client):
        """属性总和≠10 → 422"""
        response = await client.post(
            "/api/v1/game/start",
            json={
                "name": "test",
                "gender": "男",
                "talent_card_ids": ["f01", "l02", "x03"],
                "attributes": {
                    "root_bone": 5,
                    "comprehension": 5,
                    "mindset": 5,
                    "luck": 0,
                },
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_gender(self, client):
        """无效性别 → 422"""
        response = await client.post(
            "/api/v1/game/start",
            json={
                "name": "test",
                "gender": "其他",
                "talent_card_ids": ["f01", "l02", "x03"],
                "attributes": {
                    "root_bone": 3,
                    "comprehension": 3,
                    "mindset": 2,
                    "luck": 2,
                },
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_talent_ids(self, client):
        """无效天赋卡ID → 422"""
        response = await client.post(
            "/api/v1/game/start",
            json={
                "name": "test",
                "gender": "男",
                "talent_card_ids": ["invalid1", "invalid2", "invalid3"],
                "attributes": {
                    "root_bone": 3,
                    "comprehension": 3,
                    "mindset": 2,
                    "luck": 2,
                },
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_with_empty_name_returns_422(self, client):
        """空名称 → 422"""
        response = await client.post(
            "/api/v1/game/start",
            json={
                "name": "",
                "gender": "男",
                "talent_card_ids": ["f01", "l02", "x03"],
                "attributes": {
                    "root_bone": 3,
                    "comprehension": 3,
                    "mindset": 2,
                    "luck": 2,
                },
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_with_whitespace_name_returns_422(self, client):
        """纯空白名称 → 422"""
        response = await client.post(
            "/api/v1/game/start",
            json={
                "name": "   ",
                "gender": "男",
                "talent_card_ids": ["f01", "l02", "x03"],
                "attributes": {
                    "root_bone": 3,
                    "comprehension": 3,
                    "mindset": 2,
                    "luck": 2,
                },
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_with_valid_name_returns_200(self, client):
        """有效名称(叶尘) → 200 + name匹配"""
        response = await client.post(
            "/api/v1/game/start",
            json={
                "name": "叶尘",
                "gender": "男",
                "talent_card_ids": ["f01", "l02", "x03"],
                "attributes": {
                    "root_bone": 3,
                    "comprehension": 3,
                    "mindset": 2,
                    "luck": 2,
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["state"]["name"] == "叶尘"

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client):
        """缺少必填字段 → 422"""
        response = await client.post(
            "/api/v1/game/start",
            json={"name": "test"},
        )
        assert response.status_code == 422
