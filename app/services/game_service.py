"""Game service — lifecycle management, state progression, cultivation formula.

This is the core orchestration layer: it calls all other services
(talent, realm, sect, event_engine, breakthrough, scoring) and manages
the player's game session.
"""

import uuid

from app.services.talent_service import validate_selection
from app.services.realm_service import get_realm_config, get_next_realm
from app.services.event_engine import (
    load_templates,
    filter_templates,
    calculate_weights,
    select_event,
    build_event_context,
)
from app.services.scoring import determine_ending, calculate_score, get_grade
from app.models.player import PlayerState

_games: dict[str, dict] = {}


def _new_session_id() -> str:
    return uuid.uuid4().hex[:16]


def start_game(name: str, gender: str, talent_card_ids: list[str], attributes: dict) -> dict:
    if gender not in ("男", "女"):
        raise ValueError("性别必须是 '男' 或 '女'")

    valid, msg = validate_selection(talent_card_ids)
    if not valid:
        raise ValueError(msg)

    for key, val in attributes.items():
        if val < 0 or val > 10:
            raise ValueError(f"属性值必须在 0-10 之间，{key}={val}")

    total = sum(attributes.values())
    if total != 10:
        raise ValueError(f"四维属性总和必须为10，当前为{total}")

    session_id = _new_session_id()
    realm_config = get_realm_config("凡人")

    _games[session_id] = {
        "session_id": session_id,
        "name": name,
        "gender": gender,
        "attributes": {**attributes},
        "realm": "凡人",
        "realm_progress": 0.0,
        "cultivation": 0.0,
        "spirit_stones": 0,
        "age": 0,
        "lifespan": realm_config["lifespan"] if realm_config else 80,
        "faction": "",
        "talent_ids": list(talent_card_ids),
        "techniques": [],
        "technique_grades": [],
        "inventory": [],
        "is_alive": True,
        "event_count": 0,
        "ascended": False,
    }
    return _games[session_id]


def get_state(session_id: str) -> dict:
    if session_id not in _games:
        raise ValueError(f"无效的 session_id: {session_id}")
    return _games[session_id]


def _to_engine_context(state: dict) -> dict:
    return {
        "realm": state["realm"],
        "age": state["age"],
        "faction": state["faction"],
        "luck": state["attributes"]["luck"],
        "cultivation": state["cultivation"],
        "comprehension": state["attributes"]["comprehension"],
    }


def get_next_event(session_id: str) -> dict:
    state = get_state(session_id)
    ctx = _to_engine_context(state)

    templates = load_templates()
    filtered = filter_templates(templates, ctx)
    weighted = calculate_weights(filtered, ctx)
    chosen = select_event(weighted)

    event_ctx = build_event_context(chosen, ctx)

    state["_current_event"] = {
        "id": chosen.get("id", ""),
        "type": chosen.get("type", ""),
        "title": event_ctx["title"],
        "options": event_ctx["default_options"],
    }

    return {
        "event_id": chosen.get("id", ""),
        "title": event_ctx["title"],
        "narrative": event_ctx["fallback_narrative"],
        "options": event_ctx["default_options"],
    }


def _calc_cultivation_gain(event_type: str, comprehension: int, technique_grades: list[str]) -> float:
    GRADE_MODIFIER = {"凡品": 1.0, "灵品": 1.5, "玄品": 2.0, "仙品": 3.0}
    BASE_GAIN = {"daily": 10, "adventure": 30, "bottleneck": 5}

    base = BASE_GAIN.get(event_type, 10)
    comp_bonus = 1 + comprehension * 0.1
    tech_mod = 0.5
    if technique_grades:
        mods = [GRADE_MODIFIER.get(g, 0.5) for g in technique_grades]
        tech_mod = sum(mods) / len(mods)

    return base * comp_bonus * tech_mod


def _handle_cultivation_overflow(state: dict, new_cultivation: float) -> None:
    realm = state["realm"]
    next_realm = get_next_realm(realm)
    if next_realm is None:
        state["cultivation"] = new_cultivation
        return

    next_config = get_realm_config(next_realm)
    next_req = next_config.get("cultivation_req", 0) if next_config else 0

    if next_req and new_cultivation >= next_req:
        overflow = new_cultivation - next_req
        state["cultivation"] = overflow
        state["realm_progress"] = overflow / next_req
    else:
        state["cultivation"] = new_cultivation


def process_choice(session_id: str, option_id: str) -> dict:
    state = get_state(session_id)
    current_event = state.get("_current_event")
    if current_event is None:
        raise ValueError("没有当前事件，请先调用 get_next_event")

    chosen = None
    for opt in current_event["options"]:
        if opt["id"] == option_id:
            chosen = opt
            break
    if chosen is None:
        raise ValueError(f"无效的选项ID: {option_id}")

    consequences = chosen.get("consequences", {})
    spirit_stones_gain = consequences.get("spirit_stones_gain", 0)

    event_type = current_event.get("type", "daily")
    comprehension = state["attributes"]["comprehension"]
    technique_grades = state["technique_grades"]

    cultivation_gain = _calc_cultivation_gain(event_type, comprehension, technique_grades)
    new_cultivation = state["cultivation"] + cultivation_gain

    _handle_cultivation_overflow(state, new_cultivation)

    state["spirit_stones"] += spirit_stones_gain
    realm_config = get_realm_config(state["realm"])
    if realm_config:
        cap = realm_config.get("spirit_stone_cap", 0)
        if cap is not None:
            state["spirit_stones"] = min(state["spirit_stones"], cap)

        time_span = realm_config.get("time_span", 0)
        if time_span is not None:
            state["age"] += time_span

    state["event_count"] += 1
    del state["_current_event"]

    return state


def check_game_over(player_state: dict) -> bool:
    if player_state.get("ascended", False):
        return True
    age = player_state.get("age", 0)
    lifespan = player_state.get("lifespan", 0)
    event_count = player_state.get("event_count", 0)
    if age >= lifespan:
        return True
    if event_count >= 60:
        return True
    return False


def end_game(session_id: str) -> dict:
    state = get_state(session_id)
    state["is_alive"] = False

    attrs = state["attributes"]
    player = PlayerState(
        id=state["session_id"],
        name=state["name"],
        gender=state.get("gender", ""),
        root_bone=attrs["rootBone"],
        comprehension=attrs["comprehension"],
        mindset=attrs["mindset"],
        luck=attrs["luck"],
        realm=state["realm"],
        realm_progress=state.get("realm_progress", 0.0),
        lifespan=state.get("lifespan", 0),
        faction=state.get("faction", ""),
        spirit_stones=state.get("spirit_stones", 0),
        techniques=state.get("techniques", []),
        inventory=state.get("inventory", []),
        event_count=state.get("event_count", 0),
        is_alive=False,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )

    age = state.get("age", 0)
    ascended = state.get("ascended", False)
    technique_grades = state.get("technique_grades", [])

    ending = determine_ending(player, age=age, ascended=ascended)
    score = calculate_score(player, ending, age=age, technique_grades=technique_grades)
    grade = get_grade(score)

    return {
        "session_id": session_id,
        "ending": ending,
        "score": score,
        "grade": grade,
    }
