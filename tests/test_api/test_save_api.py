"""Tests for save API endpoints — event history."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.game_service import start_game, _games


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _create_test_game():
    """Helper: 创建测试游戏"""
    game = start_game(
        name="测试仙人", gender="男",
        talent_card_ids=["f01", "f02", "f03"],
        attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
    )
    return game


@pytest.mark.asyncio
async def test_events_after_creation(client):
    """创建游戏后获取事件历史，尚无事件日志时应返回空列表"""
    game = _create_test_game()
    response = await client.get(f"/api/v1/game/events/{game['session_id']}")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) == 0


@pytest.mark.asyncio
async def test_events_after_choices(client):
    """创建游戏并做出选择后，事件数量正确且按 event_index ASC 排序"""
    game = _create_test_game()
    _games[game["session_id"]]["age"] = 20  # CULTIVATOR stage

    for _ in range(3):
        event_resp = await client.post(
            "/api/v1/game/event",
            json={"player_id": game["session_id"]},
        )
        assert event_resp.status_code == 200
        event_data = event_resp.json()
        options = event_data.get("options", [])
        if not options:
            continue
        choose_resp = await client.post(
            "/api/v1/game/event/choose",
            json={"session_id": game["session_id"], "option_id": options[0]["id"]},
        )
        assert choose_resp.status_code == 200

    response = await client.get(f"/api/v1/game/events/{game['session_id']}")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    # Events are logged in process_choice — some cycles may be narrative-only
    assert len(events) >= 1

    indices = [e["event_index"] for e in events]
    assert indices == sorted(indices), "Events must be ordered by event_index ASC"


@pytest.mark.asyncio
async def test_events_not_found(client):
    """不存在的 session_id 应返回 404"""
    response = await client.get("/api/v1/game/events/nonexistent")
    assert response.status_code == 404


def _start_game_with_save(user_id: str = "test_user", save_slot: int = 1, name: str = "测试仙人"):
    return start_game(
        name=name,
        gender="男",
        talent_card_ids=["f01", "f02", "f03"],
        attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
        user_id=user_id,
        save_slot=save_slot,
    )


@pytest.mark.asyncio
async def test_start_with_save_slot(client):
    game = _start_game_with_save()
    assert game["session_id"]
    assert game["user_id"] == "test_user"
    assert game["save_slot"] == 1

    resp = await client.get(f"/api/v1/game/state/{game['session_id']}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_overwrite_save_slot(client):
    game1 = _start_game_with_save(user_id="overwrite_user", save_slot=1, name="第一个仙人")
    sid1 = game1["session_id"]

    game2 = _start_game_with_save(user_id="overwrite_user", save_slot=1, name="第二个仙人")
    sid2 = game2["session_id"]

    assert sid1 != sid2

    saves_resp = await client.get("/api/v1/game/saves", params={"user_id": "overwrite_user"})
    assert saves_resp.status_code == 200
    saves = saves_resp.json()["saves"]
    assert len(saves) == 1
    assert saves[0]["session_id"] == sid2
    assert saves[0]["name"] == "第二个仙人"

    old_resp = await client.get(f"/api/v1/game/state/{sid1}")
    assert old_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_saves(client):
    _start_game_with_save(user_id="list_user", save_slot=1, name="存档一")
    _start_game_with_save(user_id="list_user", save_slot=2, name="存档二")

    resp = await client.get("/api/v1/game/saves", params={"user_id": "list_user"})
    assert resp.status_code == 200
    saves = resp.json()["saves"]
    assert len(saves) == 2
    assert saves[0]["slot"] == 1
    assert saves[1]["slot"] == 2


@pytest.mark.asyncio
async def test_load_save(client):
    game = _start_game_with_save(user_id="load_user", save_slot=1)
    _games[game["session_id"]]["age"] = 25
    _games[game["session_id"]]["cultivation"] = 42.5
    _games[game["session_id"]]["technique_grades"] = ["天品", "地品"]
    _games[game["session_id"]]["ascended"] = True

    from app.database import get_db, init_db
    from app.repositories import game_repo
    conn = get_db()
    init_db(conn)
    try:
        game_repo.save_player(conn, _games[game["session_id"]])
        conn.commit()
    finally:
        conn.close()

    _games.pop(game["session_id"], None)

    resp = await client.post("/api/v1/game/save/load", json={
        "user_id": "load_user",
        "save_slot": 1,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == game["session_id"]
    assert data["state"]["age"] == 25
    assert data["state"]["cultivation"] == 42.5
    assert data["state"]["technique_grades"] == ["天品", "地品"]
    assert data["state"]["ascended"] is True

    state_resp = await client.get(f"/api/v1/game/state/{game['session_id']}")
    assert state_resp.status_code == 200
    state_data = state_resp.json()
    assert state_data["age"] == 25


@pytest.mark.asyncio
async def test_delete_save(client):
    _start_game_with_save(user_id="del_user", save_slot=1)

    saves_resp = await client.get("/api/v1/game/saves", params={"user_id": "del_user"})
    assert len(saves_resp.json()["saves"]) == 1

    resp = await client.delete("/api/v1/game/save/del_user/1")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    saves_resp2 = await client.get("/api/v1/game/saves", params={"user_id": "del_user"})
    assert len(saves_resp2.json()["saves"]) == 0


@pytest.mark.asyncio
async def test_backward_compat_no_user_id(client):
    game = start_game(
        name="旧玩家",
        gender="男",
        talent_card_ids=["f01", "f02", "f03"],
        attributes={"rootBone": 3, "comprehension": 3, "mindset": 2, "luck": 2},
    )
    assert game["session_id"]
    assert game["user_id"] is None

    saves_resp = await client.get("/api/v1/game/saves", params={"user_id": "anyone"})
    assert saves_resp.status_code == 200
    saves = saves_resp.json()["saves"]
    session_ids = [s["session_id"] for s in saves]
    assert game["session_id"] not in session_ids

    state_resp = await client.get(f"/api/v1/game/state/{game['session_id']}")
    assert state_resp.status_code == 200
