"""Game API router — start, state query, end game, leaderboard, events."""
from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.models.game import EndGameRequest, GameStartRequest, GameStartResponse, LeaderboardEntry
from app.models.player import PlayerState
from app.models.event import EventRequest, ChooseRequest, ChooseResponse, BreakthroughInfo, AftermathResponse
from app.repositories import game_repo
from app.services.game_service import (
    get_state,
    end_game,
    start_game,
    get_next_event,
    process_choice,
    handle_breakthrough_choice,
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
            user_id=request.user_id,
            save_slot=request.save_slot,
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
            cultivation=result.get("cultivation", 0.0),
            age=result.get("age", 0),
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
    conn = get_db()
    try:
        rows = game_repo.get_leaderboard(conn)
        return [
            LeaderboardEntry(
                rank=i + 1,
                player_name=row["name"],
                score=row["score"],
                realm=row["realm"],
                ending_id=row.get("ending_id"),
            )
            for i, row in enumerate(rows)
        ]
    finally:
        conn.close()


@router.post("/event/choose", response_model=ChooseResponse)
async def post_event_choose(request: ChooseRequest):
    try:
        state = get_state(request.session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Game session not found")

    # 突破选项：use_pill / direct → 走 handle_breakthrough_choice
    if request.option_id in ("use_pill", "direct"):
        cultivation_before = state["cultivation"]
        use_pill = request.option_id == "use_pill"
        result = handle_breakthrough_choice(state, use_pill=use_pill)

        # 持久化玩家状态和事件日志
        conn = get_db()
        try:
            game_repo.save_player(conn, state)
            event_log_data = {
                "event_index": state.get("event_count", 0),
                "event_type": "breakthrough",
                "narrative": result["breakthrough_message"],
                "options": [
                    {"id": "use_pill", "text": "服用丹药"},
                    {"id": "direct", "text": "直接突破"},
                ],
                "chosen_option_id": request.option_id,
                "consequences": {
                    "success": result["success"],
                    "new_realm": result["new_realm"],
                },
                "realm": state.get("realm", ""),
                "aftermath": {
                    "cultivation_change": state["cultivation"] - cultivation_before,
                    "age_advance": 0,
                    "narrative": result["breakthrough_message"],
                    "breakthrough": {
                        "success": result["success"],
                        "new_realm": result["new_realm"],
                        "message": result["breakthrough_message"],
                    },
                },
            }
            game_repo.save_event_log(conn, request.session_id, event_log_data)
            conn.commit()
        finally:
            conn.close()

        breakthrough_info = BreakthroughInfo(
            message=result["breakthrough_message"],
            new_realm=result["new_realm"],
            success=result["success"],
            use_pill=use_pill,
        )

        return ChooseResponse(
            state=state,
            aftermath=AftermathResponse(
                cultivation_change=state["cultivation"] - cultivation_before,
                age_advance=0,
                narrative=result["breakthrough_message"],
                breakthrough=breakthrough_info,
            ),
        )

    cultivation_before = state["cultivation"]

    try:
        new_state = process_choice(request.session_id, request.option_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service_aftermath = new_state.get("aftermath", {})
    outcome = new_state.get("_last_choice_outcome", {})

    return ChooseResponse(
        state=new_state,
        aftermath={
            "cultivation_change": new_state["cultivation"] - cultivation_before,
            "age_advance": outcome.get("age_advance", 0),
            "narrative": service_aftermath.get("narrative"),
            "breakthrough": None,
        },
    )


@router.post("/event")
async def post_event(request: EventRequest):
    try:
        state = get_state(request.player_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Game session not found")

    if not state["is_alive"] or check_game_over(state):
        raise HTTPException(status_code=400, detail="Game is already over")

    event = get_next_event(request.player_id)
    state = get_state(request.player_id)
    return {
        "narrative": event["narrative"],
        "options": event["options"],
        "has_options": len(event.get("options", [])) > 0,
        "title": event.get("title"),
        "is_breakthrough": event.get("is_breakthrough", False),
        "metadata": {"isFallback": event.get("is_fallback", False)},
        "state": state,
    }
