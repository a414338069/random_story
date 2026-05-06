"""Game service — lifecycle management, state progression, cultivation formula.

This is the core orchestration layer: it calls all other services
(talent, realm, sect, event_engine, breakthrough, scoring) and manages
the player's game session.
"""

import random
import uuid

from app.config import Settings
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
from app.services.breakthrough import attempt_breakthrough, BreakthroughResult
from app.services.ai_service import DeepSeekService, MockAIService
from app.services.life_stage import get_life_stage, get_cultivation_multiplier, can_attempt_breakthrough
from app.models.player import PlayerState
from app.repositories import game_repo
from app.database import get_db, init_db

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

    conn = get_db()
    init_db(conn)
    try:
        game_repo.save_player(conn, _games[session_id])
        conn.commit()
    finally:
        conn.close()

    return _games[session_id]


def get_state(session_id: str) -> dict:
    if session_id in _games:
        return _games[session_id]

    conn = get_db()
    try:
        state = game_repo.load_player(conn, session_id)
    finally:
        conn.close()

    if state is None:
        raise ValueError(f"无效的 session_id: {session_id}")

    _games[session_id] = state
    return state


def _to_engine_context(state: dict) -> dict:
    return {
        "realm": state["realm"],
        "age": state["age"],
        "faction": state["faction"],
        "luck": state["attributes"]["luck"],
        "cultivation": state["cultivation"],
        "comprehension": state["attributes"]["comprehension"],
        "life_stage": get_life_stage(state["age"]).value,
    }


def _get_ai_service():
    """Return the appropriate AI service based on environment configuration.

    Uses MockAIService when DEEPSEEK_API_KEY is not set (e.g. tests / CI),
    otherwise uses the real DeepSeekService.
    """
    from app.config import Settings
    settings = Settings()
    if settings.DEEPSEEK_API_KEY:
        return DeepSeekService(settings)
    return MockAIService()


def _build_ai_prompt(
    event_ctx: dict,
    state: dict,
    recent_summaries: list[dict] | None = None,
    last_outcome: dict | None = None,
) -> str:
    """Build a context-rich prompt for AI narrative generation."""
    player = event_ctx.get("player", {})
    attrs = state.get("attributes", {})

    parts = [
        "请为以下修仙世界事件生成叙事：",
        "",
        f"【当前境界】{player.get('realm', '')}",
        f"【角色年龄】{player.get('age', 0)}岁",
        f"【属性面板】根骨={attrs.get('rootBone', 0)}, 悟性={attrs.get('comprehension', 0)}, "
        f"心性={attrs.get('mindset', 0)}, 气运={attrs.get('luck', 0)}",
        f"【所属势力】{state.get('faction', '无')}",
        f"【事件类型】{event_ctx.get('event_type', '')}",
        f"【事件标题】{event_ctx.get('title', '')}",
        f"【事件模板】{event_ctx.get('prompt', '')}",
    ]

    breakthrough_msg = state.get("_breakthrough_msg")
    if breakthrough_msg:
        parts.append(f"【特殊状态】{breakthrough_msg}")

    if recent_summaries:
        parts.append("")
        parts.append("【近期经历】")
        for i, summary in enumerate(reversed(recent_summaries), 1):
            event_desc = summary.get("narrative", "未知事件")
            if len(event_desc) > 120:
                event_desc = event_desc[:120] + "..."
            parts.append(f"  {i}. {event_desc}")

    if last_outcome:
        parts.append("")
        parts.append("【上一轮结果】")
        parts.append(f"  选择了: {last_outcome.get('chosen_text', '未知')}")
        cult_change = last_outcome.get("cultivation_change", 0)
        if cult_change >= 0:
            parts.append(f"  修为变化: +{cult_change:.1f}")
        else:
            parts.append(f"  修为变化: {cult_change:.1f}")
        parts.append(f"  年龄增长: {last_outcome.get('age_advance', 0)}年")

    if event_ctx.get("narrative_only"):
        parts.append("")
        parts.append("【叙事模式】本次事件为纯叙事推进，不要返回选项，options返回空数组。")

    parts.append("")
    parts.append("请延续以上事件脉络，生成与上一件事自然衔接的叙事和选项。不要让新事件完全从零开始。")

    return "\n".join(parts)


def get_next_event(session_id: str) -> dict:
    state = get_state(session_id)
    ctx = _to_engine_context(state)

    templates = load_templates()
    filtered = filter_templates(templates, ctx)
    weighted = calculate_weights(filtered, ctx)
    chosen = select_event(weighted, state)

    event_ctx = build_event_context(chosen, ctx)

    narrative = event_ctx["fallback_narrative"]
    options = event_ctx["default_options"]
    is_fallback = True

    conn = get_db()
    try:
        recent_summaries = game_repo.get_recent_event_summaries(conn, session_id, limit=5)
    finally:
        conn.close()

    try:
        ai_service = _get_ai_service()
        prompt = _build_ai_prompt(
            event_ctx, state,
            recent_summaries=recent_summaries,
            last_outcome=state.get("_last_choice_outcome"),
        )

        # Check breakthrough warning and inject into prompt
        warning = _check_breakthrough_warning(state)
        if warning:
            prompt += f"\n\n【突破预警】{warning['message']}"

        skip_ai = bool(event_ctx.get("narrative_only")) and bool(event_ctx.get("fallback_narrative"))
        ai_result = ai_service.generate_event(prompt=prompt, context=state, skip_ai=skip_ai)

        if ai_result and isinstance(ai_result, dict) and ai_result.get("narrative"):
            narrative = ai_result["narrative"]
            ai_options = ai_result.get("options", [])
            if ai_options:
                cleaned = []
                for opt in ai_options:
                    if isinstance(opt, dict):
                        # 验证并保留consequences（白名单验证）
                        raw_consequences = opt.get("consequences", {})
                        safe_consequences = {}
                        if isinstance(raw_consequences, dict):
                            if "spirit_stones_gain" in raw_consequences:
                                val = raw_consequences["spirit_stones_gain"]
                                if isinstance(val, (int, float)):
                                    safe_consequences["spirit_stones_gain"] = max(-100, min(100, int(val)))
                            if "cultivation_gain" in raw_consequences:
                                val = raw_consequences["cultivation_gain"]
                                if isinstance(val, (int, float)):
                                    safe_consequences["cultivation_gain"] = max(0, min(200, int(val)))
                        cleaned.append({
                            "id": opt.get("id", ""),
                            "text": opt.get("text", ""),
                            "consequences": safe_consequences,
                        })
                if cleaned:
                    options = cleaned
                    is_fallback = False
            elif event_ctx.get("narrative_only"):
                options = []
                is_fallback = False
    except Exception:
        pass

    state["_current_narrative"] = narrative
    state["_current_event"] = {
        "id": chosen.get("id", ""),
        "type": chosen.get("type", ""),
        "title": event_ctx["title"],
        "options": options,
        "narrative_only": event_ctx.get("narrative_only", False),
    }

    return {
        "event_id": chosen.get("id", ""),
        "title": event_ctx["title"],
        "narrative": narrative,
        "options": options,
        "is_fallback": is_fallback,
    }


CONSEQUENCE_TEMPLATES = {
    "cultivation_positive": [
        "你{action_desc}，一股温热的灵力自丹田涌出，经脉微微颤动，修为提升了{cult_change}点。",
        "{action_desc}后，你感到灵台清明，对大道的感悟又深了一层，修为增长{cult_change}点。",
        "灵气如涓涓细流汇入体内，你{action_desc}，修为精进{cult_change}点。",
        "你{action_desc}，体内真元缓缓壮大，丹田中灵气充盈，修为增加{cult_change}点。",
        "静心凝神，你{action_desc}，天地灵气在周身流转，修为提升{cult_change}点。",
    ],
    "cultivation_negative": [
        "你{action_desc}，但心神不宁，灵气外泄，修为损失{cult_change_abs}点。",
        "一番波折后，你{action_desc}，却因岔气导致真元紊乱，修为下降{cult_change_abs}点。",
    ],
    "narrative_only": [
        "岁月流转，{time_desc}。你在平淡中有所感悟，修为精进{cult_change}点。",
        "时光飞逝，{time_desc}过去了。你虽未刻意修炼，但修为也缓慢增长了{cult_change}点。",
        "{time_desc}的光阴悄然逝去，你在日常的点滴中体悟着修行之道，修为提升{cult_change}点。",
        "又是一{time_unit}，{time_desc}平平淡淡地度过了，修为缓慢增长了{cult_change}点。",
    ],
    "breakthrough": [
        "你{action_desc}，体内灵力突然暴动——{breakthrough_msg}！修为变化{cult_change}点。",
        "就在你{action_desc}之际，{breakthrough_msg}！周身灵气激荡，修为变化{cult_change}点。",
    ],
}


def _build_consequence_narrative(
    chosen_text: str,
    cultivation_gain: float,
    time_span: int | None,
    spirit_stones_gain: int = 0,
    breakthrough_msg: str | None = None,
) -> str:
    """构建丰富的后果叙事文本。"""
    cult_change_str = f"+{cultivation_gain:.1f}" if cultivation_gain >= 0 else f"{cultivation_gain:.1f}"
    cult_change_abs = f"{abs(cultivation_gain):.1f}"

    # 时间描述
    if time_span and time_span > 0:
        if time_span >= 10:
            time_desc = f"{time_span}年"
            time_unit = "段漫长岁月"
        else:
            time_desc = f"{time_span}年"
            time_unit = "年"
    else:
        time_desc = ""
        time_unit = "段时间"

    # 灵石描述
    stones_part = ""
    if spirit_stones_gain > 0:
        stones_part = f"，获得{spirit_stones_gain}枚灵石"
    elif spirit_stones_gain < 0:
        stones_part = f"，消耗{abs(spirit_stones_gain)}枚灵石"

    # 选择模板
    if breakthrough_msg:
        template = random.choice(CONSEQUENCE_TEMPLATES["breakthrough"])
        return template.format(
            action_desc=chosen_text if chosen_text else "冥冥中感受到突破的契机",
            breakthrough_msg=breakthrough_msg,
            cult_change=cult_change_str,
        ) + stones_part

    if not chosen_text:  # narrative_only
        template = random.choice(CONSEQUENCE_TEMPLATES["narrative_only"])
        result = template.format(
            time_desc=time_desc,
            time_unit=time_unit,
            cult_change=cult_change_str,
        )
        if cultivation_gain <= 0:
            result = result.replace("精进", "变化").replace("提升", "变化").replace("增长", "变化")
        return result + stones_part

    # 普通选择
    if cultivation_gain >= 0:
        template = random.choice(CONSEQUENCE_TEMPLATES["cultivation_positive"])
    else:
        template = random.choice(CONSEQUENCE_TEMPLATES["cultivation_negative"])

    action_desc = f"选择了「{chosen_text}」"
    return template.format(
        action_desc=action_desc,
        cult_change=cult_change_str,
        cult_change_abs=cult_change_abs,
    ) + stones_part + (f"，{time_desc}过去了。" if time_desc else "")


def _calc_cultivation_gain(event_type: str, comprehension: int, technique_grades: list[str], age: int) -> float:
    GRADE_MODIFIER = {"凡品": 1.0, "灵品": 1.5, "玄品": 2.0, "仙品": 3.0}
    BASE_GAIN = {"daily": 10, "adventure": 30, "bottleneck": 5}

    base = BASE_GAIN.get(event_type, 10)
    comp_bonus = 1 + comprehension * 0.1
    tech_mod = 0.5
    if technique_grades:
        mods = [GRADE_MODIFIER.get(g, 0.5) for g in technique_grades]
        tech_mod = sum(mods) / len(mods)

    return base * comp_bonus * tech_mod * get_cultivation_multiplier(age)


def _check_breakthrough_warning(state: dict) -> dict | None:
    """Check if cultivation is approaching breakthrough threshold (80%).

    Returns a warning dict if cultivation >= 80% of next realm requirement,
    or None if no warning needed.
    """
    realm = state.get("realm", "")
    next_realm = get_next_realm(realm)
    if next_realm is None:
        return None

    next_config = get_realm_config(next_realm)
    if not next_config:
        return None

    next_req = next_config.get("cultivation_req", 0)
    if not next_req:
        return None

    threshold = next_req * 0.8
    cultivation = state.get("cultivation", 0)

    if cultivation >= threshold:
        return {
            "message": f"修为将至突破之境（{cultivation:.0f}/{next_req}），需谨慎行事",
            "threshold": threshold,
            "current": cultivation,
        }

    return None


def _handle_cultivation_overflow(state: dict, new_cultivation: float) -> None:
    realm = state["realm"]
    age = state.get("age", 0)

    next_realm = get_next_realm(realm)
    if next_realm is None:
        state["cultivation"] = new_cultivation
        return

    next_config = get_realm_config(next_realm)
    next_req = next_config.get("cultivation_req", 0) if next_config else 0

    if next_req and new_cultivation >= next_req:
        if not can_attempt_breakthrough(age):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("突破被年龄阻止 (age=%d < 16)，修为封顶在 %d", age, next_req - 1)
            state["cultivation"] = next_req - 1
            state["realm_progress"] = (next_req - 1) / next_req
            return

        # 修为达到下一境界门槛，触发突破判定
        state["cultivation"] = new_cultivation  # 临时写入供 attempt_breakthrough 读取
        result = attempt_breakthrough(state)

        if result.success:
            old_realm = state["realm"]
            state["realm"] = result.new_realm
            new_realm_config = get_realm_config(result.new_realm)
            if new_realm_config and isinstance(new_realm_config.get("lifespan"), (int, float)):
                state["lifespan"] = new_realm_config["lifespan"]
            overflow = new_cultivation - next_req
            state["cultivation"] = overflow
            state["realm_progress"] = overflow / next_req
            if result.ascended:
                state["ascended"] = True
            state["_breakthrough_msg"] = f"突破成功！从{old_realm}晋升至{result.new_realm}！"
        else:
            cultivation_after = max(0, new_cultivation - result.cultivation_loss)
            state["cultivation"] = cultivation_after
            state["realm_progress"] = 0.0
            if result.realm_dropped:
                state["realm"] = result.new_realm
                state["_breakthrough_msg"] = f"突破失败！修为跌落至{result.new_realm}，损失{result.cultivation_loss:.0f}点修为！"
            else:
                state["_breakthrough_msg"] = f"突破失败！损失{result.cultivation_loss:.0f}点修为！"
    else:
        state["cultivation"] = new_cultivation


def process_choice(session_id: str, option_id: str | None = None) -> dict:
    state = get_state(session_id)
    current_event = state.get("_current_event")
    if current_event is None:
        raise ValueError("没有当前事件，请先调用 get_next_event")

    chosen = None
    consequences: dict = {}

    if option_id is None:
        if not current_event.get("narrative_only"):
            raise ValueError("narrative_only 事件才允许 auto-advance，请提供 option_id")
        age = state["age"]
        cultivation_gain = 5.0 if age >= 12 else 0.0
        consequences = {"cultivation_gain": cultivation_gain, "age_advance": True}
    else:
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

    explicit_gain = consequences.get("cultivation_gain")
    if explicit_gain is not None:
        cultivation_gain = explicit_gain * (1 + comprehension * 0.03)
    else:
        cultivation_gain = _calc_cultivation_gain(event_type, comprehension, technique_grades, state["age"])
    new_cultivation = state["cultivation"] + cultivation_gain

    _handle_cultivation_overflow(state, new_cultivation)

    # 灵石余额检查 - 降级处理而非拒绝
    if spirit_stones_gain < 0 and state["spirit_stones"] + spirit_stones_gain < 0:
        spirit_stones_gain = -state["spirit_stones"]
    state["spirit_stones"] = max(0, state["spirit_stones"] + spirit_stones_gain)

    faction_assign = consequences.get("faction_assign")
    if faction_assign and isinstance(faction_assign, str):
        state["faction"] = faction_assign

    realm_config = get_realm_config(state["realm"])
    if realm_config:
        cap = realm_config.get("spirit_stone_cap", 0)
        if cap is not None:
            state["spirit_stones"] = min(state["spirit_stones"], cap)

        time_span = realm_config.get("time_span", 0)
        if time_span is not None:
            state["age"] += time_span

    state["event_count"] += 1

    # 安静年追踪：非安静年递增，安静年重置
    if current_event.get("id") == "quiet_year":
        state["_consecutive_events"] = 0
    else:
        state["_consecutive_events"] = state.get("_consecutive_events", 0) + 1

    event_log_data = {
        "event_index": state["event_count"],
        "event_type": current_event.get("type", ""),
        "narrative": state.get("_current_narrative", current_event.get("title", "")),
        "options": current_event.get("options", []),
        "chosen_option_id": option_id,
        "consequences": consequences,
    }

    del state["_current_event"]
    state.pop("_current_narrative", None)

    conn = get_db()
    init_db(conn)
    try:
        game_repo.save_player(conn, state)
        game_repo.save_event_log(conn, session_id, event_log_data)
        conn.commit()
    finally:
        conn.close()

    # Store outcome for AI prompt enrichment in next event
    if option_id is None:
        chosen_text = ""
    else:
        chosen_text = chosen.get("text", "") if chosen else ""
    time_span = realm_config.get("time_span", 0) if realm_config else 0
    state["_last_choice_outcome"] = {
        "chosen_text": chosen_text,
        "cultivation_change": cultivation_gain,
        "age_advance": time_span,
        "consequences_applied": consequences,
    }

    # Build consequence narrative (no AI call needed)
    consequence_narrative = _build_consequence_narrative(
        chosen_text=chosen_text,
        cultivation_gain=cultivation_gain,
        time_span=time_span,
        spirit_stones_gain=spirit_stones_gain,
        breakthrough_msg=state.get("_breakthrough_msg"),
    )

    breakthrough_info = None
    breakthrough_msg = state.get("_breakthrough_msg")
    if breakthrough_msg:
        breakthrough_info = {"message": breakthrough_msg}

    # Append aftermath data to state for API response
    state["aftermath"] = {
        "narrative": consequence_narrative,
        "breakthrough": breakthrough_info,
    }

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

    conn = get_db()
    init_db(conn)
    try:
        game_repo.save_player(conn, state)
        conn.commit()
    finally:
        conn.close()

    return {
        "session_id": session_id,
        "ending": ending,
        "score": score,
        "grade": grade,
    }
