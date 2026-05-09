"""Game API router — start, state query, end game, leaderboard, events."""
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.models.game import EndGameRequest, GameStartRequest, GameStartResponse, LeaderboardEntry
from app.models.player import PlayerState
from app.models.event import EventRequest, ChooseRequest, ChooseResponse, BreakthroughInfo, AftermathResponse
from app.repositories import game_repo
from app.services.event_factory import generate_event as factory_generate_event
from app.services.game_service import (
    get_state,
    end_game,
    start_game,
    get_next_event,
    process_choice,
    handle_breakthrough_choice,
    check_game_over,
    prepare_stream_event,
    _get_ai_service,
)

logger = logging.getLogger(__name__)
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


@router.post("/event/stream")
async def post_event_stream(request: EventRequest):
    """SSE streaming endpoint — streams narrative token-by-token for L3/L4 events.

    L1/L2 (deterministic) events return the full result as SSE events.
    L3/L4 (AI-generated) events stream narrative chunks in real time.
    """
    try:
        state = get_state(request.player_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Game session not found")

    if not state["is_alive"] or check_game_over(state):
        raise HTTPException(status_code=400, detail="Game is already over")

    prep = prepare_stream_event(request.player_id)

    if prep.get("_breakthrough"):
        bt_event = prep["breakthrough_event"]

        async def _bt_generator():
            yield _sse_event("narrative_done", {"narrative": bt_event.get("narrative", "")})
            yield _sse_event("options", {"options": bt_event.get("options", [])})
            yield _sse_event("done", {"status": "complete"})

        return StreamingResponse(
            _bt_generator(),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )

    state = prep["state"]
    event_ctx = prep["event_ctx"]
    prompt = prep["prompt"]
    tier = prep["tier"]
    chosen = prep["chosen"]

    if tier in ("L1", "L2"):
        ai_service = _get_ai_service()
        result = factory_generate_event(event_ctx, state, ai_service, prompt)
        narrative = result.get("narrative", event_ctx.get("fallback_narrative", ""))
        options = result.get("options", event_ctx.get("default_options", []))

        _done_state_tracking(state, event_ctx, chosen, narrative, options)

        async def _l1l2_generator():
            yield _sse_event("narrative_done", {"narrative": narrative})
            yield _sse_event("options", {"options": options})
            yield _sse_event("done", {"status": "complete"})

        return StreamingResponse(
            _l1l2_generator(),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )

    async def _stream_generator():
        narrative_parts: list[str] = []
        options: list[dict] = []

        try:
            ai_service = _get_ai_service()
            async for chunk in ai_service.generate_event_stream(prompt=prompt, context=state):
                if chunk.get("type") == "narrative_chunk":
                    text = chunk.get("text", "")
                    narrative_parts.append(text)
                    yield _sse_event("narrative_chunk", {"text": text})
                elif chunk.get("type") == "options":
                    raw_opts = chunk.get("options")
                    options = list(raw_opts) if isinstance(raw_opts, list) else []
                    full_narrative = "".join(narrative_parts)
                    yield _sse_event("narrative_done", {"narrative": full_narrative})
                    yield _sse_event("options", {"options": options})

            full_narrative = "".join(narrative_parts)
            _done_state_tracking(state, event_ctx, chosen, full_narrative, options)
            yield _sse_event("done", {"status": "complete"})
        except Exception as e:
            logger.warning("SSE stream error for player %s: %s", request.player_id, e)
            yield _sse_event("error", {"error": str(e)})
            yield _sse_event("done", {"status": "error"})

    return StreamingResponse(
        _stream_generator(),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _sse_headers() -> dict:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


def _done_state_tracking(state: dict, event_ctx: dict, chosen: dict, narrative: str, options: list[dict]) -> None:
    narrative_only = bool(event_ctx.get("narrative_only")) and len(options) == 0
    if narrative_only:
        state["event_count"] += 1
        state["_consecutive_events"] = state.get("_consecutive_events", 0) + 1
    state["_current_narrative"] = narrative
    state["_current_event"] = {
        "id": chosen.get("id", ""),
        "type": chosen.get("type", ""),
        "title": event_ctx["title"],
        "options": options,
        "narrative_only": narrative_only,
    }
