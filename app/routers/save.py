"""Save/load API router — event history, save/load game state."""
from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.repositories import game_repo
from app.models.save import SaveListResponse, SaveSlotInfo, SaveLoadRequest, SaveLoadResponse
from app.models.player import PlayerState
from app.services.game_service import list_saves, load_save, delete_save

router = APIRouter(prefix="/api/v1/game", tags=["save"])


@router.get("/events/{session_id}")
async def get_event_history(session_id: str):
    """获取事件历史"""
    conn = get_db()
    try:
        player = game_repo.load_player(conn, session_id)
        if player is None:
            raise HTTPException(status_code=404, detail="Game session not found")
        events = game_repo.get_event_logs(conn, session_id)
        return events
    finally:
        conn.close()


@router.get("/saves", response_model=SaveListResponse)
async def get_saves(user_id: str):
    saves = list_saves(user_id)
    return SaveListResponse(
        saves=[SaveSlotInfo(**s) for s in saves]
    )


@router.post("/save/load", response_model=SaveLoadResponse)
async def load_save_endpoint(request: SaveLoadRequest):
    try:
        state = load_save(request.user_id, request.save_slot)
    except ValueError:
        raise HTTPException(status_code=404, detail="Save not found")

    player_state = PlayerState(
        id=state["session_id"],
        name=state.get("name", ""),
        gender=state.get("gender", ""),
        talent_ids=state.get("talent_ids", []),
        root_bone=state["attributes"].get("rootBone", 0),
        comprehension=state["attributes"].get("comprehension", 0),
        mindset=state["attributes"].get("mindset", 0),
        luck=state["attributes"].get("luck", 0),
        realm=state.get("realm", ""),
        realm_progress=state.get("realm_progress", 0.0),
        cultivation=state.get("cultivation", 0.0),
        age=state.get("age", 0),
        health=state.get("health", 100.0),
        qi=state.get("qi", 0.0),
        lifespan=state.get("lifespan", 100),
        faction=state.get("faction", ""),
        spirit_stones=state.get("spirit_stones", 0),
        techniques=state.get("techniques", []),
        inventory=state.get("inventory", []),
        event_count=state.get("event_count", 0),
        score=state.get("score", 0),
        technique_grades=state.get("technique_grades", []),
        ascended=state.get("ascended", False),
        is_alive=state.get("is_alive", True),
        user_id=state.get("user_id"),
        save_slot=state.get("save_slot", 0),
    )
    return SaveLoadResponse(session_id=state["session_id"], state=player_state)


@router.delete("/save/{user_id}/{save_slot}")
async def delete_save_endpoint(user_id: str, save_slot: int):
    delete_save(user_id, save_slot)
    return {"success": True}
