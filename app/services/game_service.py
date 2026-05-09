"""Game service — lifecycle management, state progression, cultivation formula.

This is the core orchestration layer: it calls all other services
(talent, realm, sect, event_engine, breakthrough, scoring) and manages
the player's game session.
"""

import json
import logging
import random
import uuid

from app.services.talent_service import load_talents, validate_selection, get_active_modifiers, _apply_talent_attr_bonuses
from app.services.realm_service import get_realm_config, get_next_realm
from app.services.event_engine import (
    load_templates,
    filter_templates,
    calculate_weights,
    select_event,
    build_event_context,
    _get_realm_tier,
)
from app.services.scoring import determine_ending, calculate_score, get_grade
from app.services.breakthrough import attempt_breakthrough, BreakthroughResult, build_breakthrough_event
from app.services.ai_service import DeepSeekService, MockAIService
from app.services.ai_validator import check_narrative_option_alignment
from app.services.cache_service import get_cached, set_cached
from app.services.context_engine import determine_scenario_pool, match_scenarios
from app.services.event_factory import should_use_ai, generate_event as factory_generate_event
from app.services.life_stage import get_life_stage, get_cultivation_multiplier, can_attempt_breakthrough
from app.services import sect_service
from app.models.memory import StoryMemory, StoryMemorySet
from app.models.player import PlayerState
from app.models.tags import Tag, TagSet, TagCategory
from app.repositories import game_repo
from app.database import get_db, init_db

_games: dict[str, dict] = {}
_ai_service_instance = None


def _new_session_id() -> str:
    return uuid.uuid4().hex[:16]


def _bootstrap_tags(state: dict) -> TagSet:
    """Derive initial tags from existing player state (for old saves)."""
    tags = TagSet()
    tags.add(Tag(category=TagCategory.IDENTITY, key="name", value=f"姓名={state.get('name', '')}"))
    tags.add(Tag(category=TagCategory.IDENTITY, key="gender", value=f"性别={state.get('gender', '')}"))
    tags.add(Tag(category=TagCategory.IDENTITY, key="age_group", value=f"年龄={state.get('age', 0)}岁"))

    faction = state.get("faction", "")
    if faction:
        tags.add(Tag(category=TagCategory.IDENTITY, key="faction", value=f"门派={faction}"))
    else:
        tags.add(Tag(category=TagCategory.IDENTITY, key="identity", value="散修"))

    techniques = state.get("techniques", [])
    for tech in techniques:
        if tech:
            tags.add(Tag(category=TagCategory.SKILL, key=f"tech_{tech}", value=f"功法={tech}"))

    inventory = state.get("inventory", [])
    for item in inventory:
        if item:
            tags.add(Tag(category=TagCategory.STATE, key=f"item_{item}", value=f"物品={item}"))

    tags.add(Tag(category=TagCategory.STATE, key="realm_current", value=f"境界={state.get('realm', '凡人')}"))

    return tags


def _ensure_tags_and_memory(state: dict) -> None:
    """Bootstrap tags/story_memory if missing (e.g. old saves from before the tag system).

    Never crashes — graceful degradation on bootstrap failure.
    """
    _logger = logging.getLogger(__name__)
    try:
        if state.get("tags") is None:
            state["tags"] = _bootstrap_tags(state)
        if state.get("story_memory") is None:
            state["story_memory"] = StoryMemorySet()
    except Exception:
        _logger.warning("标签引导失败，使用空标签")


def _random_sect_for_player(attributes: dict) -> str:
    """Pick a random sect that the player meets the join conditions for.

    If no sect conditions are met, returns ``"散修"``.

    Args:
        attributes: Dict with camelCase keys (rootBone, comprehension, mindset, luck).

    Returns:
        The name of a randomly selected eligible sect, or ``"散修"``.
    """
    eligible_sects = []
    for sect in sect_service.load_sects():
        name = sect.get("name", "")
        if not name or name == "散修":
            continue
        if sect_service.check_join_conditions(attributes, name):
            eligible_sects.append(name)
    if eligible_sects:
        return random.choice(eligible_sects)
    return "散修"


def start_game(
    name: str,
    gender: str,
    talent_card_ids: list[str],
    attributes: dict,
    user_id: str | None = None,
    save_slot: int | None = None,
) -> dict:
    if not name or not name.strip():
        raise ValueError("姓名不能为空")

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

    # Apply talent attribute bonuses (snake_case key mapping)
    snake_attrs = {
        "root_bone": attributes.get("rootBone", 0),
        "comprehension": attributes.get("comprehension", 0),
        "mindset": attributes.get("mindset", 0),
        "luck": attributes.get("luck", 0),
    }
    enhanced_snake = _apply_talent_attr_bonuses(talent_card_ids, snake_attrs)
    enhanced_attrs = {
        "rootBone": enhanced_snake["root_bone"],
        "comprehension": enhanced_snake["comprehension"],
        "mindset": enhanced_snake["mindset"],
        "luck": enhanced_snake["luck"],
    }

    conn = get_db()
    init_db(conn)
    try:
        if user_id and save_slot is not None:
            row = conn.execute(
                "SELECT id FROM players WHERE user_id = ? AND save_slot = ?",
                (user_id, save_slot),
            ).fetchone()
            if row:
                old_id = row["id"]
                conn.execute("DELETE FROM event_logs WHERE player_id = ?", (old_id,))
                conn.execute("DELETE FROM players WHERE id = ?", (old_id,))
                _games.pop(old_id, None)
                conn.commit()

        session_id = _new_session_id()
        realm_config = get_realm_config("凡人")

        _games[session_id] = {
            "session_id": session_id,
            "name": name,
            "gender": gender,
            "attributes": {**enhanced_attrs},
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
            "user_id": user_id,
            "save_slot": save_slot if save_slot is not None else 0,
        }

        state = _games[session_id]
        tags = TagSet()
        tags.add(Tag(
            category=TagCategory.IDENTITY,
            key="name",
            value=f"姓名={name}",
            description=f"角色姓名: {name}",
        ))
        tags.add(Tag(
            category=TagCategory.IDENTITY,
            key="gender",
            value=f"性别={gender}",
            description=f"角色性别: {gender}",
        ))
        tags.add(Tag(
            category=TagCategory.IDENTITY,
            key="age_group",
            value="年龄=0",
        ))

        all_talents = load_talents()
        talent_map = {t["id"]: t["name"] for t in all_talents}
        for tid in talent_card_ids:
            tname = talent_map.get(tid, tid)
            tags.add(Tag(
                category=TagCategory.BOND,
                key=f"talent_{tname}",
                value=f"天赋={tname}",
                description=f"先天拥有天赋: {tname}",
                priority=2,
            ))

        faction = state.get("faction", "")
        if faction:
            tags.add(Tag(
                category=TagCategory.IDENTITY,
                key="faction",
                value=f"门派={faction}",
                description=f"所属门派: {faction}",
            ))

        state["tags"] = tags
        state["story_memory"] = StoryMemorySet()

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

    _ensure_tags_and_memory(state)
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
        "consecutive_events": state.get("_consecutive_events", 0),
        "tags": state.get("tags"),
    }


def _get_ai_service():
    """Return the appropriate AI service based on environment configuration.

    Uses MockAIService when DEEPSEEK_API_KEY is not set (e.g. tests / CI),
    otherwise uses the real DeepSeekService.

    Singleton: the same service instance is reused across requests to avoid
    creating a new OpenAI client on every call.
    """
    global _ai_service_instance
    if _ai_service_instance is not None:
        return _ai_service_instance
    from app.config import Settings
    settings = Settings()
    if settings.DEEPSEEK_API_KEY:
        _ai_service_instance = DeepSeekService(settings)
    else:
        _ai_service_instance = MockAIService()
    return _ai_service_instance


def _format_talent_names(talent_ids: list[str]) -> str:
    if not talent_ids:
        return "无"
    all_talents = load_talents()
    talent_map = {t["id"]: t["name"] for t in all_talents}
    names = [talent_map.get(tid, tid) for tid in talent_ids]
    return "、".join(names)


def _build_ai_prompt(
    event_ctx: dict,
    state: dict,
    recent_summaries: list[dict] | None = None,
    last_outcome: dict | None = None,
) -> str:
    """Build a context-rich prompt for AI narrative generation."""
    player = event_ctx.get("player", {})
    attrs = state.get("attributes", {})
    realm_tier = _get_realm_tier(player.get('realm', ''))

    parts = [
        "请为以下修仙世界事件生成叙事：",
        "",
        f"【当前境界】{player.get('realm', '')}",
        f"【境界层级】{realm_tier}",
        f"【角色年龄】{player.get('age', 0)}岁",
        f"【属性面板】根骨={attrs.get('rootBone', 0)}, 悟性={attrs.get('comprehension', 0)}, "
        f"心性={attrs.get('mindset', 0)}, 气运={attrs.get('luck', 0)}",
        f"【所属势力】{state.get('faction', '无')}",
        f"【天赋】{_format_talent_names(state.get('talent_ids', []))}",
    ]

    tags = state.get("tags")
    if isinstance(tags, TagSet) and len(tags.tags) > 0:
        parts.append("")
        parts.append(tags.to_context_string())

    story_memory = state.get("story_memory")
    if isinstance(story_memory, StoryMemorySet) and len(story_memory.memories) > 0:
        mem_str = story_memory.to_prompt_context()
        if mem_str:
            parts.append("")
            parts.append(mem_str)

    parts.extend([
        f"【事件类型】{event_ctx.get('event_type', '')}",
        f"【事件标题】{event_ctx.get('title', '')}",
        f"【事件模板】{event_ctx.get('prompt', '')}",
    ])

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
    parts.append("【选项约束 — 必须遵守】")
    parts.append("1. 叙事一致性：叙事中出现的具体人物、物品、地点、事件类型，必须在至少一个选项中体现或回应。")
    parts.append("2. 行为合理性：每个选项必须是叙事上下文中该角色的合理行为选择，不能凭空出现叙事未提及的动作。")
    parts.append("3. 关键词覆盖：选项文本中应包含叙事中的至少一个关键名词（人物名、物品名、地点名或核心事件词）。")
    parts.append("4. 差异化：选项之间的consequence_preview必须反映不同结果方向，禁止相同结果的不同描述。")
    parts.append("")
    parts.append("【违规示例 — 禁止】")
    parts.append('- 叙事："老者看中你的灵草，想用丹药交换" → 错误选项："购买丹药"（叙事中老者要交换而非你购买）')
    parts.append('- 叙事："深山中遇到妖兽袭击" → 错误选项："去集市购物"（与叙事完全无关）')
    parts.append("")
    parts.append("【正确示例 — 参考】")
    parts.append('- 叙事："老者看中你的灵草，想用丹药交换" → 正确选项："出售灵草"、"拒绝交易"、"讨价还价"')
    parts.append('- 叙事："深山中遇到妖兽袭击" → 正确选项："与之战斗"、"迅速逃跑"、"攀上树躲避"')
    parts.append("")
    parts.append("请基于【事件标题】和【事件模板】生成独立的叙事内容。叙事应与事件标题紧密相关，选项应与事件主题匹配。可以自然提及角色的过往经历，但叙事的核心必须是当前事件本身。")

    return "\n".join(parts)


def prepare_stream_event(session_id: str) -> dict:
    """Prepare event context for SSE streaming endpoint.

    Selects template, advances age, builds AI prompt, determines tier.
    Does NOT call AI or set _current_event/_current_narrative —
    the caller (SSE endpoint) handles generation and final state tracking.
    """
    state = get_state(session_id)

    if state.get("_pending_breakthrough"):
        return {"_breakthrough": True, "state": state, "breakthrough_event": build_breakthrough_event(state)}

    ctx = _to_engine_context(state)

    templates = load_templates()
    filtered = filter_templates(templates, ctx)
    weighted = calculate_weights(filtered, ctx)

    if weighted:
        template_dicts = [t for t, _ in weighted]
        scenarios = determine_scenario_pool(state.get("tags"), ctx)
        matched_scenarios_list = match_scenarios(template_dicts, scenarios)
        if matched_scenarios_list:
            matched_ids = {id(t) for t in matched_scenarios_list}
            weighted = [(t, w) for t, w in weighted if id(t) in matched_ids]

    chosen = select_event(weighted, state)

    realm_config = get_realm_config(state["realm"])
    time_span = realm_config.get("time_span", 1) if realm_config else 1
    if time_span is None:
        time_span = 1
    state["age"] += time_span
    ctx["age"] = state["age"]

    event_ctx = build_event_context(chosen, ctx)
    event_ctx["template"] = chosen

    conn = get_db()
    try:
        recent_summaries = game_repo.get_recent_event_summaries(conn, session_id, limit=5)
    finally:
        conn.close()

    prompt = _build_ai_prompt(
        event_ctx, state,
        recent_summaries=recent_summaries,
        last_outcome=state.get("_last_choice_outcome"),
    )

    warning = _check_breakthrough_warning(state)
    if warning:
        prompt += f"\n\n【突破预警】{warning['message']}"

    tier = should_use_ai(event_ctx, state)

    seen_ids = state.get("_seen_event_ids", [])
    event_id = chosen.get("id", "")
    if event_id:
        seen_ids.append(event_id)
        state["_seen_event_ids"] = seen_ids[-20:]

    return {
        "state": state,
        "event_ctx": event_ctx,
        "prompt": prompt,
        "tier": tier,
        "chosen": chosen,
    }


def get_next_event(session_id: str) -> dict:
    state = get_state(session_id)

    # 检查是否有待处理的突破事件
    if state.get("_pending_breakthrough"):
        return build_breakthrough_event(state)

    ctx = _to_engine_context(state)

    templates = load_templates()
    filtered = filter_templates(templates, ctx)
    weighted = calculate_weights(filtered, ctx)

    # ── Scenario matching via context_engine ──
    if weighted:
        template_dicts = [t for t, _ in weighted]
        scenarios = determine_scenario_pool(state.get("tags"), ctx)
        matched_scenarios_list = match_scenarios(template_dicts, scenarios)
        if matched_scenarios_list:
            matched_ids = {id(t) for t in matched_scenarios_list}
            weighted = [(t, w) for t, w in weighted if id(t) in matched_ids]

    chosen = select_event(weighted, state)

    # 先推进年龄，确保 build_event_context 中的 {age} 使用新值
    realm_config = get_realm_config(state["realm"])
    time_span = realm_config.get("time_span", 1) if realm_config else 1
    if time_span is None:
        time_span = 1
    state["age"] += time_span

    # 衰减 STATE 标签的 TTL（中毒、顿悟等临时状态自然过期）
    tags = state.get("tags")
    if tags and hasattr(tags, "age_tags"):
        tags.age_tags(time_span)

    # 更新 ctx 中的 age 以匹配已推进的年龄
    ctx["age"] = state["age"]

    event_ctx = build_event_context(chosen, ctx)
    event_ctx["template"] = chosen  # for factory's tier decision

    narrative = event_ctx["fallback_narrative"]
    options = event_ctx["default_options"]
    is_fallback = True

    conn = get_db()
    try:
        recent_summaries = game_repo.get_recent_event_summaries(conn, session_id, limit=5)
    finally:
        conn.close()

    # ── Event factory: tier-based generation with cascade fallback ──
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

        tier = should_use_ai(event_ctx, state)

        # Check AI result cache: key = {template_id}:{realm}:{tier}
        cache_template_id = chosen.get('id', '')
        cache_realm = state['realm']
        cached = get_cached(cache_template_id, cache_realm, tier)

        if cached and isinstance(cached, dict) and cached.get("narrative"):
            narrative = cached["narrative"]
            cached_options = cached.get("options", [])
            if cached_options:
                options = cached_options
                is_fallback = False
            elif event_ctx.get("narrative_only"):
                options = []
                is_fallback = False
        else:
            factory_result = factory_generate_event(event_ctx, state, ai_service, prompt)
            used_tier = factory_result.get("_tier", tier)

            if factory_result and isinstance(factory_result, dict) and factory_result.get("narrative"):
                narrative = factory_result["narrative"]
                ai_options = factory_result.get("options", [])
                if ai_options:
                    cleaned = []
                    for opt in ai_options:
                        if isinstance(opt, dict):
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
                        if check_narrative_option_alignment(narrative, cleaned):
                            options = cleaned
                            is_fallback = False
                            # Cache validated AI result by tier
                            set_cached(cache_template_id, cache_realm, used_tier,
                                       {"narrative": narrative, "options": options})
                        else:
                            # Alignment check failed — still use AI options but don't cache
                            options = cleaned
                            logging.getLogger(__name__).warning(
                                "options-narrative alignment check failed, using AI options uncached"
                            )
                elif event_ctx.get("narrative_only"):
                    options = []
                    is_fallback = False
                elif used_tier in ("L1", "L2"):
                    # L1/L2 results are deterministic, treat as non-fallback
                    options = ai_options
                    is_fallback = False
            elif event_ctx.get("narrative_only") and event_ctx.get("fallback_narrative"):
                # L1/L2 results came back empty but we have fallback
                pass  # keep narrative from event_ctx["fallback_narrative"]
    except Exception:
        logging.getLogger(__name__).warning("AI 叙事生成异常，使用默认叙事和选项")

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

    seen_ids = state.get("_seen_event_ids", [])
    event_id = chosen.get("id", "")
    if event_id:
        seen_ids.append(event_id)
        state["_seen_event_ids"] = seen_ids[-20:]

    return {
        "event_id": chosen.get("id", ""),
        "title": event_ctx["title"],
        "narrative": narrative,
        "options": options,
        "is_fallback": is_fallback,
    }


def _parse_tag_spec(tag_spec) -> Tag | None:
    """Parse a tag specification from option consequences into a Tag object.

    Supports two formats:
      - String: ``"category:key=value"`` (e.g. ``"state:injured"``, ``"bond:master=拜师青云真人"``)
      - Dict: ``{"category":"state", "key":"injured", "value":"受伤"}``

    Returns ``None`` if parsing fails (malformed input, invalid category, etc.).
    """
    if isinstance(tag_spec, dict):
        try:
            category = TagCategory(tag_spec.get("category", "state"))
            return Tag(
                category=category,
                key=tag_spec.get("key", ""),
                value=tag_spec.get("value", ""),
                description=tag_spec.get("description", ""),
            )
        except (ValueError, KeyError, TypeError):
            return None

    if isinstance(tag_spec, str):
        parts = tag_spec.split(":", 1)
        if len(parts) != 2:
            return None
        cat_str, rest = parts
        kv = rest.split("=", 1)
        key = kv[0] if len(kv) >= 1 else ""
        value = kv[1] if len(kv) >= 2 else ""
        try:
            category = TagCategory(cat_str)
        except ValueError:
            return None
        return Tag(category=category, key=key, value=value)

    return None


def _persist_tags(state: dict, session_id: str) -> None:
    """Persist tag changes to SQLite. Graceful degradation on failure."""
    try:
        conn = get_db()
        try:
            game_repo.save_player(conn, state)
            conn.commit()
        finally:
            conn.close()
    except Exception:
        logging.getLogger(__name__).warning("标签持久化失败: session_id=%s", session_id)


CONSEQUENCE_TEMPLATES = {
    "cultivation_positive": [
        "{action_desc}，一股温热的灵力自丹田涌出，经脉微微颤动，修为提升了{cult_change}点。",
        "{action_desc}后，你感到灵台清明，对大道的感悟又深了一层，修为增长{cult_change}点。",
        "灵气如涓涓细流汇入体内，{action_desc}，修为精进{cult_change}点。",
        "{action_desc}，体内真元缓缓壮大，丹田中灵气充盈，修为增加{cult_change}点。",
        "静心凝神，{action_desc}，天地灵气在周身流转，修为提升{cult_change}点。",
    ],
    "cultivation_negative": [
        "{action_desc}，但心神不宁，灵气外泄，修为损失{cult_change_abs}点。",
        "一番波折后，{action_desc}，却因岔气导致真元紊乱，修为下降{cult_change_abs}点。",
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
    ai_service=None,
    event_context: dict | None = None,
) -> str:
    """构建丰富的后果叙事文本，优先使用AI生成，模板兜底。"""
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

    # AI-first aftermath generation (skip for breakthrough events)
    if ai_service is not None and event_context is not None and not breakthrough_msg:
        _logger = logging.getLogger(__name__)
        try:
            current_narrative = event_context.get("narrative", "")
            event_type = event_context.get("type", "")
            event_title = event_context.get("title", "")
            # Build aftermath context for AI
            aftermath_ctx = {
                "title": event_title,
                "event_type": event_type,
                "narrative": current_narrative,
                "chosen_text": chosen_text,
                "cultivation_gain": cultivation_gain,
                "spirit_stones_gain": spirit_stones_gain,
                "realm": event_context.get("realm", ""),
                "age": event_context.get("age", 0),
            }
            ai_result = ai_service.generate_aftermath(aftermath_ctx)
            if ai_result and isinstance(ai_result, dict) and ai_result.get("narrative"):
                _logger.info("Using AI-generated aftermath narrative")
                return ai_result["narrative"]
        except Exception:
            _logger.warning("AI aftermath generation failed, falling back to template")

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

    action_desc = chosen_text if chosen_text else "不知如何是好"
    return template.format(
        action_desc=action_desc,
        cult_change=cult_change_str,
        cult_change_abs=cult_change_abs,
    ) + stones_part + (f"，{time_desc}过去了。" if time_desc else "")


def _calc_cultivation_gain(event_type: str, comprehension: int, technique_grades: list[str], age: int, talent_ids: list[str] | None = None) -> float:
    GRADE_MODIFIER = {"凡品": 1.0, "灵品": 1.5, "玄品": 2.0, "仙品": 3.0}
    BASE_GAIN = {"daily": 10, "adventure": 30, "bottleneck": 5}

    base = BASE_GAIN.get(event_type, 10)
    comp_bonus = 1 + comprehension * 0.1
    tech_mod = 0.5
    if technique_grades:
        mods = [GRADE_MODIFIER.get(g, 0.5) for g in technique_grades]
        tech_mod = sum(mods) / len(mods)

    talent_mod = 1.0
    if talent_ids:
        modifiers = get_active_modifiers(talent_ids)
        talent_mod = 1 + modifiers.get("cultivation_speed", 0.0) + modifiers.get("learning_speed", 0.0)

    return base * comp_bonus * tech_mod * get_cultivation_multiplier(age) * talent_mod


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
            logger = logging.getLogger(__name__)
            logger.warning("突破被年龄阻止 (age=%d < 16)，修为封顶在 %d", age, next_req - 1)
            state["cultivation"] = next_req - 1
            state["realm_progress"] = (next_req - 1) / next_req
            return

        # 修为达到下一境界门槛，暂停突破等待玩家选择
        state["_breakthrough_cultivation"] = new_cultivation
        state["_breakthrough_next_req"] = next_req
        state["cultivation"] = next_req - 1
        state["realm_progress"] = (next_req - 1) / next_req
        state["_pending_breakthrough"] = True
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
        cultivation_gain = _calc_cultivation_gain("daily", state["attributes"]["comprehension"], state["technique_grades"], state["age"], state.get("talent_ids", []))
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
        cultivation_gain = _calc_cultivation_gain(event_type, comprehension, technique_grades, state["age"], state.get("talent_ids", []))

    next_realm = get_next_realm(state["realm"])
    if next_realm:
        next_config = get_realm_config(next_realm)
        next_req = next_config.get("cultivation_req", 0) if next_config else 0
        if next_req:
            max_single_gain = (next_req - state["cultivation"]) * 0.5
            if max_single_gain > 0:
                cultivation_gain = min(cultivation_gain, max(10, max_single_gain))

    new_cultivation = state["cultivation"] + cultivation_gain

    _handle_cultivation_overflow(state, new_cultivation)

    # 灵石余额检查 - 降级处理而非拒绝
    if spirit_stones_gain < 0 and state["spirit_stones"] + spirit_stones_gain < 0:
        spirit_stones_gain = -state["spirit_stones"]
    state["spirit_stones"] = max(0, state["spirit_stones"] + spirit_stones_gain)

    faction_assign = consequences.get("faction_assign")
    if faction_assign and isinstance(faction_assign, str):
        _logger = logging.getLogger(__name__)
        if faction_assign == "随机分配":
            faction_assign = _random_sect_for_player(state["attributes"])
        state["faction"] = faction_assign
        if faction_assign != "散修":
            if not sect_service.check_join_conditions(state["attributes"], faction_assign):
                _logger.warning(
                    "门派加入条件不满足: faction=%s, attributes=%s, 降级为散修",
                    faction_assign, state["attributes"],
                )
                state["faction"] = "散修"
        if state["faction"] != "散修":
            techs = sect_service.get_sect_techniques(state["faction"])
            for tech in techs:
                if tech.get("name") and tech.get("name") not in state.get("techniques", []):
                    state.setdefault("techniques", []).append(tech["name"])
                if tech.get("grade") and tech.get("grade") not in state.get("technique_grades", []):
                    state.setdefault("technique_grades", []).append(tech["grade"])

    # ── Tag updates from option consequences ──
    tag_add = consequences.get("tag_add", [])
    tag_remove = consequences.get("tag_remove", [])
    tags = state.get("tags")
    tags_changed = False
    tags_involved: list[str] = []
    if tags is not None and (tag_add or tag_remove):
        for tag_spec in tag_add:
            tag = _parse_tag_spec(tag_spec)
            if tag:
                tags.add(tag)
                tags_involved.append(tag.key)
        for key in tag_remove:
            if isinstance(key, str):
                tags.remove(key)
        tags_changed = True
        _persist_tags(state, session_id)

    # ── StoryMemory entry ──
    memory_text = chosen.get("text", "事件推进") if chosen else "岁月流逝"
    template_id = current_event.get("id", "unknown")
    memory = StoryMemory(
        event_id=template_id,
        summary=f"{current_event.get('title', '事件')}: {memory_text[:60]}",
        tags_involved=tags_involved,
        happened_at_age=state["age"],
        emotional_weight=3.0 if memory_text else 2.0,
    )
    story_memory = state.get("story_memory")
    if story_memory is not None:
        story_memory.add(memory)
    else:
        state["story_memory"] = StoryMemorySet()
        state["story_memory"].add(memory)

    realm_config = get_realm_config(state["realm"])
    if realm_config:
        cap = realm_config.get("spirit_stone_cap", 0)
        if cap is not None:
            state["spirit_stones"] = min(state["spirit_stones"], cap)

    state["event_count"] += 1

    # 安静年追踪：非安静年递增，安静年重置
    if current_event.get("id") == "quiet_year":
        state["_consecutive_events"] = 0
    else:
        state["_consecutive_events"] = state.get("_consecutive_events", 0) + 1

    # Compute aftermath data
    if option_id is None:
        chosen_text = ""
    else:
        chosen_text = chosen.get("text", "") if chosen else ""
    time_span = realm_config.get("time_span", 0) if realm_config else 0

    aftermath_event_ctx = {
        "narrative": state.get("_current_narrative", ""),
        "type": current_event.get("type", ""),
        "title": current_event.get("title", ""),
        "realm": state.get("realm", ""),
        "age": state.get("age", 0),
    }

    consequence_narrative = _build_consequence_narrative(
        chosen_text=chosen_text,
        cultivation_gain=cultivation_gain,
        time_span=time_span,
        spirit_stones_gain=spirit_stones_gain,
        ai_service=_get_ai_service(),
        event_context=aftermath_event_ctx,
    )

    aftermath = {
        "cultivation_change": cultivation_gain,
        "age_advance": time_span,
        "narrative": consequence_narrative,
        "breakthrough": None,
    }

    event_log_data = {
        "event_index": state["event_count"],
        "event_type": current_event.get("type", ""),
        "narrative": state.get("_current_narrative", current_event.get("title", "")),
        "options": current_event.get("options", []),
        "chosen_option_id": option_id,
        "consequences": consequences,
        "realm": state.get("realm", ""),
        "aftermath": aftermath,
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
    state["_last_choice_outcome"] = {
        "chosen_text": chosen_text,
        "cultivation_change": cultivation_gain,
        "age_advance": time_span,
        "consequences_applied": consequences,
    }

    # Append aftermath data to state for API response
    state["aftermath"] = aftermath

    return state


def handle_breakthrough_choice(state: dict, use_pill: bool) -> dict:
    if use_pill:
        inventory = state.get("inventory", [])
        if "breakthrough_pill" in inventory:
            inventory.remove("breakthrough_pill")
            state["inventory"] = inventory

    result = attempt_breakthrough(state, use_pill=use_pill)
    state.pop("_pending_breakthrough", None)

    if result.success:
        old_realm = state["realm"]
        state["realm"] = result.new_realm
        # 突破成功：设置冷却标记，防止瓶颈事件立即触发
        state["_breakthrough_event_count"] = state.get("event_count", 0)
        new_realm_config = get_realm_config(result.new_realm)
        if new_realm_config and isinstance(new_realm_config.get("lifespan"), (int, float)):
            state["lifespan"] = new_realm_config["lifespan"]
        next_req = state.pop("_breakthrough_next_req", 0)
        pre_cap_cult = state.pop("_breakthrough_cultivation", 0)
        # 突破成功：新境界修为 = 突破前修为 - 旧境界消耗(cultivation_req)
        # 保留大部分修为，只扣除旧境界的门槛作为突破消耗
        current_realm_config = get_realm_config(old_realm)
        current_req = current_realm_config.get("cultivation_req", 0) if current_realm_config else 0
        retained = max(0, pre_cap_cult - current_req)
        state["cultivation"] = retained
        next_next_config = get_realm_config(result.new_realm)
        next_next_req = next_next_config.get("cultivation_req", 0) if next_next_config else 1
        state["realm_progress"] = retained / next_next_req if next_next_req else 0.0
        if result.ascended:
            state["ascended"] = True
        state["_breakthrough_msg"] = f"突破成功！从{old_realm}晋升至{result.new_realm}！"
    else:
        cultivation_after = max(0, state["cultivation"] - result.cultivation_loss)
        state["cultivation"] = cultivation_after
        state["realm_progress"] = 0.0
        if result.realm_dropped:
            state["realm"] = result.new_realm
            state["_breakthrough_msg"] = f"突破失败！修为跌落至{result.new_realm}，损失{result.cultivation_loss:.0f}点修为！"
        else:
            state["_breakthrough_msg"] = f"突破失败！损失{result.cultivation_loss:.0f}点修为！"

    # 突破结果用于响应后立即清除，防止泄漏到后续AI提示词
    msg = state.pop("_breakthrough_msg", "")

    return {
        "success": result.success,
        "new_realm": result.new_realm,
        "cultivation_loss": result.cultivation_loss,
        "realm_dropped": result.realm_dropped,
        "ascended": result.ascended,
        "breakthrough_message": msg,
    }


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

    # Persist score and ending to DB so leaderboard reads correct values
    state["score"] = score
    state["ending_id"] = ending

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


def list_saves(user_id: str) -> list[dict]:
    conn = get_db()
    init_db(conn)
    try:
        rows = conn.execute(
            "SELECT id, name, realm, age, event_count, last_active_at, is_alive, save_slot "
            "FROM players WHERE user_id = ? AND is_alive = 1 ORDER BY save_slot",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "slot": row["save_slot"],
            "session_id": row["id"],
            "name": row["name"],
            "realm": row["realm"],
            "age": row["age"],
            "event_count": row["event_count"],
            "last_active_at": row["last_active_at"],
            "is_alive": bool(row["is_alive"]),
        }
        for row in rows
    ]


def load_save(user_id: str, save_slot: int) -> dict:
    conn = get_db()
    init_db(conn)
    try:
        row = conn.execute(
            "SELECT * FROM players WHERE user_id = ? AND save_slot = ?",
            (user_id, save_slot),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise ValueError(f"存档不存在: user_id={user_id}, slot={save_slot}")

    state = game_repo._db_row_to_state(row)
    _ensure_tags_and_memory(state)
    _games[state["session_id"]] = state
    return state


def delete_save(user_id: str, save_slot: int) -> None:
    conn = get_db()
    init_db(conn)
    try:
        row = conn.execute(
            "SELECT id FROM players WHERE user_id = ? AND save_slot = ?",
            (user_id, save_slot),
        ).fetchone()
        if row:
            old_id = row["id"]
            conn.execute("DELETE FROM event_logs WHERE player_id = ?", (old_id,))
            conn.execute("DELETE FROM players WHERE id = ?", (old_id,))
            conn.commit()
            _games.pop(old_id, None)
    finally:
        conn.close()
