"""Game API router — start, state query, end game, leaderboard, events."""
from fastapi import APIRouter, HTTPException

from app.models.game import EndGameRequest, GameStartRequest, GameStartResponse, LeaderboardEntry
from app.models.player import PlayerState
from app.models.event import EventRequest, ChooseRequest
from app.services.game_service import (
    get_state,
    end_game,
    start_game,
    get_next_event,
    process_choice,
    check_game_over,
)

router = APIRouter(prefix="/api/v1/game", tags=["game"])


@router.post("/start", response_model=GameStartResponse, status_code=201)
async def create_game(request: GameStartRequest):
    """创建新游戏"""
    try:
        attrs = request.attributes
        attributes = {
            "rootBone": attrs.root_bone,
            "comprehension": attrs.comprehension,
            "mindset": attrs.mindset,
            "luck": attrs.luck,
        }
        result = start_game(
            name=request.name,
            gender=request.gender,
            talent_card_ids=request.talent_card_ids,
            attributes=attributes,
        )
        state = PlayerState(
            id=result["session_id"],
            name=result["name"],
            gender=result.get("gender", ""),
            talent_ids=result.get("talent_ids", []),
            root_bone=result["attributes"]["rootBone"],
            comprehension=result["attributes"]["comprehension"],
            mindset=result["attributes"]["mindset"],
            luck=result["attributes"]["luck"],
            realm=result["realm"],
            realm_progress=result.get("realm_progress", 0.0),
            health=100.0,
            qi=0.0,
            lifespan=result.get("lifespan", 100),
            faction=result.get("faction", ""),
            spirit_stones=result.get("spirit_stones", 0),
            techniques=result.get("techniques", []),
            inventory=result.get("inventory", []),
            event_count=result.get("event_count", 0),
            score=0,
            is_alive=result.get("is_alive", True),
        )
        return GameStartResponse(session_id=result["session_id"], state=state)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/state/{session_id}")
async def get_game_state(session_id: str):
    """查询当前游戏状态"""
    try:
        state = get_state(session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Game session not found")
    return state


@router.post("/end")
async def end_game_endpoint(request: EndGameRequest):
    """结算游戏"""
    try:
        result = end_game(request.session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Game session not found")
    if result is None:
        raise HTTPException(status_code=404, detail="Game session not found")
    return result


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard():
    """排行榜"""
    return []


@router.post("/event/choose")
async def post_event_choose(request: ChooseRequest):
    try:
        state = get_state(request.session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Game session not found")

    cultivation_before = state["cultivation"]
    age_before = state["age"]

    try:
        new_state = process_choice(request.session_id, request.option_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "state": new_state,
        "aftermath": {
            "cultivation_change": new_state["cultivation"] - cultivation_before,
            "age_advance": new_state["age"] - age_before,
        },
    }


@router.post("/event")
async def post_event(request: EventRequest):
    try:
        state = get_state(request.player_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Game session not found")

    if not state["is_alive"] or check_game_over(state):
        raise HTTPException(status_code=400, detail="Game is already over")

    event = get_next_event(request.player_id)
    return {
        "narrative": event["narrative"],
        "options": event["options"],
        "metadata": {"isFallback": True},
    }
