"""Event factory — 4-tier AI layered generation strategy with cascade fallback.

Tier definitions:
  L1 (rule-based) : narrative_only, childhood, birth, youth — pre-written pool, no AI
  L2 (template)   : daily, economy, emotional, stones, sect — format strings with context
  L3 (v4-flash)   : adventure, combat, social, explore, heavenly, fortune — fast AI
  L4 (v4-pro)     : bottleneck, breakthrough, key decisions — high-quality AI

Cascade fallback:
  L4 fails → retry with L3 → L1
  L3 fails → retry with L1
  L1 / L2 are deterministic and never fail

Soft cap: after 30 events, auto-downgrade to L2 regardless of event type.
"""

from __future__ import annotations

import json
import logging
import random
import time

_logger = logging.getLogger(__name__)

_EMPTY_RESULT: dict = {"narrative": "", "options": []}

_MODEL_FLASH = "deepseek-v4-flash"
_MODEL_PRO = "deepseek-v4-pro"

_AI_CALL_BUDGET_PER_SESSION = 100
_ai_call_counts: dict[str, int] = {}


def get_ai_call_count(session_id: str) -> int:
    return _ai_call_counts.get(session_id, 0)


def reset_ai_call_count(session_id: str) -> None:
    _ai_call_counts.pop(session_id, None)

_L1_NARRATIVES_DAILY = [
    "日子如水般流过，你每日在山中砍柴挑水，日出而作，日落而息。虽然辛苦，却也磨砺了心志。",
    "这一年平平淡淡地过去了。你在田埂间劳作，偶尔抬头看天边云卷云舒，心中偶尔闪过一丝对远方的向往。",
    "山中岁月静好，你没有遇到什么大事，在日复一日的劳作中，体魄愈发强健。",
    "你静静地度过了这段时光。修行之路漫长，平凡的日子也自有其意义。",
    "晨起练体，暮归修行。日子虽单调，但你心中始终燃着一团不灭的火焰。",
    "这些日子里，你过着最普通不过的生活。砍柴、挑水、修炼——简单的事重复做，也是一种修行。",
    "夏日的蝉鸣声里，你坐在山石上打坐，四周灵气虽稀薄，却也有几分清宁。",
    "又是一个寻常的日子，你在修行与劳作之间寻找着微妙的平衡。",
    "日子一天天过去，你在平凡的日常中积累着力量。水滴石穿，非一日之功。",
]

_L1_NARRATIVES_CHILDHOOD = [
    "你还是个孩子，世界在你眼中充满新奇。你在村中奔跑嬉戏，偶尔听老人讲起修仙者的传说，眼中闪着向往的光。",
    "那些童年的记忆如同褪色的水墨画——你在泥土中打滚，在山泉中嬉水，从未想过有朝一日会走上修仙之路。",
    "村里的孩子们都在玩耍，你却喜欢一个人蹲在山脚下，静静地看着天边的云，仿佛在等待什么。",
    "你还年幼，不懂什么叫修行。但每当你仰望星空，总有一种说不清的悸动——仿佛那些星辰在呼唤着你。",
    "童年是无忧无虑的。你在田埂上追蝴蝶，在小溪边抓鱼，偶尔听大人说起山外的世界，心中种下一颗好奇的种子。",
    "你渐渐长大了。村里人都说这孩子有些不一样——总是一个人沉浸在自己的世界里，偶尔说出些大人也难以理解的话。",
]

_L1_NARRATIVES_BIRTH = [
    "你出生在一个普通的小山村。接生婆说你哭声洪亮，将来必成大器——当然，每个孩子的父母都听过这样的话。",
    "伴随着一声响亮的啼哭，你来到了这个世界。屋外大雪纷飞，屋内炉火温暖，父母脸上满是喜悦。",
]

_L1_NARRATIVES_QUIET = [
    "这一年风调雨顺，你在山中静修，虽无大事，但根基更加稳固。",
    "日子平静如水。你日出而作、日落而息，修行虽慢但踏实。",
    "山中无甲子，寒尽不知年。这一年平静得仿佛时间停滞。",
    "这一年过得波澜不惊，你在默默修行中度过。修行的路上，有时平淡也是一种积累。",
    "四季轮转，岁月静好。这一年没有特别的际遇，但也并非虚度。你的心境在平静中愈发通透。",
    "时光悄然流逝，你在安静的修行中沉淀着修为。没有惊心动魄，只有持之以恒。",
]

_L2_TEMPLATES: dict = {
    "daily": {
        "narratives": [
            "又到了平凡的一天。你在{location}修炼，周围灵气{quality}。{cultivation_desc}",
            "清晨的阳光洒在{location}，你开始了日复一日的修炼。{cultivation_desc}",
            "在{location}的日子平淡而充实，你按部就班地修行着，{cultivation_desc}",
            "这一天和往常一样，你在{location}打坐吐纳。{quality}的灵气缓缓流入经脉。",
        ],
        "options": [
            {"id": "opt1", "text": "继续修炼", "consequences": {"cultivation_gain": 5}},
            {"id": "opt2", "text": "休息调整", "consequences": {"cultivation_gain": 2}},
            {"id": "opt3", "text": "外出散步", "consequences": {"cultivation_gain": 3}},
        ],
    },
    "economy": {
        "narratives": [
            "集市上人来人往，你看到了几个摊位在卖{items}。价格还算公道。",
            "一位商人路过{location}，带来了远方的货物。{items}的品质颇为不错。",
            "你路过坊市的交易处，今日的{items}比往常多了一些。",
        ],
        "options": [
            {"id": "opt1", "text": "购买修炼所需", "consequences": {"spirit_stones_gain": -10, "cultivation_gain": 5}},
            {"id": "opt2", "text": "讨价还价", "consequences": {"spirit_stones_gain": -5, "cultivation_gain": 2}},
            {"id": "opt3", "text": "离开集市", "consequences": {}},
        ],
    },
    "emotional": {
        "narratives": [
            "夜幕降临，你独自坐在{location}，心中泛起一丝惆怅。修行之路漫漫，不知何时才能有大成。",
            "看着同门师兄弟进步神速，你心中不免有些焦急。但转念一想，每个人的道都不同。",
            "你回忆起这些年的修行历程，有得有失，有苦有甜，心中百感交集。",
        ],
        "options": [
            {"id": "opt1", "text": "静心修炼，不与人争", "consequences": {"cultivation_gain": 5}},
            {"id": "opt2", "text": "请教前辈指点迷津", "consequences": {"cultivation_gain": 8}},
            {"id": "opt3", "text": "独自冥思感悟", "consequences": {"cultivation_gain": 3}},
        ],
    },
    "stones": {
        "narratives": [
            "你在{location}附近发现了一些散落的灵石碎屑，虽不多但也有用。",
            "清理洞府时，你在角落发现了几枚被你遗忘的灵石，虽品相一般但聊胜于无。",
            "你与一位散修交易，用一些杂物换到了几枚灵石。",
        ],
        "options": [
            {"id": "opt1", "text": "收入囊中备用", "consequences": {"spirit_stones_gain": 5}},
            {"id": "opt2", "text": "直接用来修炼", "consequences": {"spirit_stones_gain": -5, "cultivation_gain": 15}},
            {"id": "opt3", "text": "赠予有缘之人", "consequences": {"spirit_stones_gain": -5}},
        ],
    },
    "sect": {
        "narratives": [
            "今日是{location}的例课，长老讲解了修行的基本法门，你受益匪浅。",
            "宗门牌前贴出了新的任务告示。你仔细看了看，有几项倒是适合你当前的实力。",
            "几位同门在{location}的广场上切磋武艺，你站在一旁观战，颇有所得。",
        ],
        "options": [
            {"id": "opt1", "text": "接取宗门任务", "consequences": {"cultivation_gain": 5}},
            {"id": "opt2", "text": "专心听长老讲道", "consequences": {"cultivation_gain": 8}},
            {"id": "opt3", "text": "与同门切磋", "consequences": {"cultivation_gain": 4}},
        ],
    },
}

def should_use_ai(event_ctx: dict, state: dict | None = None) -> str:
    """Determine the AI tier for event generation.

    Returns one of: ``"L1"`` | ``"L2"`` | ``"L3"`` | ``"L4"``.

    Args:
        event_ctx: Event context from ``event_engine.build_event_context()``.
                   Must contain at minimum an ``event_type`` key, and may
                   carry the original template under a ``template`` key.
        state: Game state dict. Used for ``event_count`` soft cap.

    Decision matrix:

    =======  ================================================
    Tier     Triggers
    =======  ================================================
    L1       ``narrative_only=True``, ``type in (childhood,
             birth, youth)``, or explicit ``event_tier="L1"``
    L4       ``type="bottleneck"`` (critical breakthrough moments)
    L3       ``type in (adventure, combat, social, explore,
             heavenly, fortune)``
    L2       ``type in (daily, economy, emotional, stones, sect)``
    L2       Soft cap: ``event_count >= 30`` overrides to L2
    =======  ================================================
    """
    template = event_ctx.get("template", event_ctx)
    event_type: str = template.get("type") or event_ctx.get("event_type", "daily")
    narrative_only: bool = bool(
        template.get("narrative_only") or event_ctx.get("narrative_only", False)
    )
    event_tier: str = template.get("event_tier", "L3")

    if narrative_only:
        return "L1"
    if event_type in ("childhood", "birth", "youth", "narrative"):
        return "L1"
    if event_tier == "L1":
        return "L1"

    if state and state.get("event_count", 0) >= 30:
        return "L2"

    if event_type == "bottleneck":
        return "L4"

    # Honor explicit event_tier when template has prompt_template (e.g. sect templates
    # with type="sect"/"daily" + event_tier="L3" should use AI, not L2 fallback)
    if event_tier in ("L3", "L4") and template.get("prompt_template"):
        return event_tier

    if event_type in ("adventure", "combat", "social", "explore", "heavenly", "fortune"):
        return "L3"

    if event_type in ("daily", "economy", "emotional", "stones", "sect"):
        return "L2"

    return event_tier


def generate_l1_narrative(event_ctx: dict) -> dict:
    """Return a pre-written narrative and default options (no AI call).

    Selects from in-memory pools keyed by event type, falling back to
    the YAML ``fallback_narrative`` if no pool entry matches.
    """
    event_type: str = event_ctx.get("event_type") or event_ctx.get("template", {}).get("type", "daily")
    narrative_only: bool = bool(event_ctx.get("narrative_only", False))
    default_options: list[dict] = list(event_ctx.get("default_options", []))
    fallback: str = event_ctx.get("fallback_narrative", "")

    if event_type in ("birth",):
        pool = _L1_NARRATIVES_BIRTH
    elif event_type in ("childhood",):
        pool = _L1_NARRATIVES_CHILDHOOD
    elif event_type in ("narrative",) or narrative_only:
        pool = _L1_NARRATIVES_QUIET
    else:
        pool = _L1_NARRATIVES_DAILY

    narrative = fallback if fallback else (random.choice(pool) if pool else "")

    result: dict = {"narrative": narrative}

    if narrative_only:
        result["options"] = []
    elif default_options:
        result["options"] = default_options
    else:
        result["options"] = [
            {"id": "opt1", "text": "继续修炼", "consequences": {"cultivation_gain": 5}},
            {"id": "opt2", "text": "稍作休息", "consequences": {"cultivation_gain": 2}},
        ]

    result["_tier"] = "L1"
    return result


def generate_l2_template(event_ctx: dict, state: dict | None = None) -> dict:
    """Generate narrative via pre-written templates filled with player context.

    No AI call — uses format strings with keys derived from player state
    (realm, location, cultivation progress, etc.).
    """
    event_type: str = event_ctx.get("event_type") or event_ctx.get("template", {}).get("type", "daily")
    fallback: str = event_ctx.get("fallback_narrative", "")
    default_options: list[dict] = list(event_ctx.get("default_options", []))
    player: dict = event_ctx.get("player", {})

    realm = player.get("realm", "凡人") if player else "凡人"

    fmt = {
        "location": _fmt_location(state, realm),
        "quality": _fmt_spirit_quality(state, realm),
        "cultivation_desc": _fmt_cultivation_desc(event_ctx, state),
        "items": _fmt_items(realm),
        "realm": realm,
    }

    tpl_config = _L2_TEMPLATES.get(event_type, _L2_TEMPLATES["daily"])
    narrative_template = random.choice(tpl_config.get("narratives", [""]))
    narrative = narrative_template.format(**fmt) if narrative_template else fallback

    tpl_options = tpl_config.get("options")
    if tpl_options:
        import copy
        options = copy.deepcopy(tpl_options)
    elif default_options:
        options = list(default_options)
    else:
        options = [
            {"id": "opt1", "text": "继续修炼", "consequences": {"cultivation_gain": 5}},
            {"id": "opt2", "text": "稍作休息", "consequences": {"cultivation_gain": 2}},
        ]

    return {"narrative": narrative, "options": options, "_tier": "L2"}


def _fmt_location(state: dict | None, realm: str) -> str:
    if state and state.get("faction"):
        return state["faction"]
    if "炼气" in realm or "筑基" in realm:
        return "宗门后山"
    if "金丹" in realm or "元婴" in realm:
        return "洞府之中"
    if "化神" in realm or "合体" in realm:
        return "灵脉之上"
    if "大乘" in realm or "渡劫" in realm:
        return "九天之上"
    return "山间"


def _fmt_spirit_quality(state: dict | None, realm: str) -> str:
    if "凡人" in realm:
        return "稀薄却纯净"
    if "炼气" in realm:
        return "渐渐凝聚"
    if "筑基" in realm:
        return "逐渐浓郁"
    if "金丹" in realm or "元婴" in realm:
        return "十分充沛"
    return "浩瀚如海"


def _fmt_cultivation_desc(event_ctx: dict, state: dict | None) -> str:
    if not state:
        return "你感到修为有所精进"
    progress = state.get("realm_progress", 0)
    if progress > 0.8:
        return "你隐约感到突破的契机正在接近"
    if progress > 0.5:
        return "修为稳步增长，经脉愈发通畅"
    if progress > 0.2:
        return "灵力在丹田中缓缓汇聚"
    return "修行刚刚起步，前路仍漫长"


def _fmt_items(realm: str) -> str:
    if "凡人" in realm:
        return "草药和兽皮"
    if "炼气" in realm:
        return "低阶丹药和灵材"
    if "筑基" in realm:
        return "中阶灵器和功法残卷"
    return "高阶丹药和稀有灵宝"


def _call_deepseek(model: str, prompt: str, max_retries: int = 2) -> dict:
    """Call the DeepSeek API directly with the given *model*.

    Returns a parsed-JSON dict on success, or ``_EMPTY_RESULT`` on
    parse/connection failure.  Raises ``RuntimeError`` when no API key
    is configured (which signals the cascade to fall back).
    """
    from app.config import Settings
    from app.services.ai_service import SYSTEM_PROMPT
    from openai import APIConnectionError, APIError, OpenAI

    settings = Settings()
    if not settings.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek API key not configured")

    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        timeout=10.0,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    t0 = time.monotonic()
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=500,
            )
            content = response.choices[0].message.content
            if not content or content.strip() == "":
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return dict(_EMPTY_RESULT)
            elapsed = time.monotonic() - t0
            _logger.info(
                "AI call ok model=%s attempt=%d latency=%.1fs",
                model, attempt + 1, elapsed,
            )
            return json.loads(content)
        except json.JSONDecodeError as e:
            _logger.error("AI returned invalid JSON (model=%s): %s", model, e)
            return dict(_EMPTY_RESULT)
        except (APIError, APIConnectionError) as e:
            _logger.warning(
                "AI API error (model=%s, attempt %d/%d): %s",
                model, attempt + 1, max_retries + 1, e,
            )
            if attempt < max_retries:
                time.sleep(2 ** attempt + 1)
        except Exception as e:
            _logger.warning("Unexpected AI error (model=%s): %s", model, e)
            if attempt < max_retries:
                time.sleep(1)

    return dict(_EMPTY_RESULT)


def _call_ai_with_fallback(
    ai_service,
    prompt: str,
    state: dict,
    tier: str,
) -> dict | None:
    """Attempt AI generation via the configured *ai_service*.

    Returns a result dict on success, or ``None`` when the call fails.
    The calling code cascades to L1 (rule-based) fallback on failure.
    """
    if ai_service is not None:
        try:
            result = ai_service.generate_event(prompt=prompt, context=state)
            if result and isinstance(result, dict) and result.get("narrative"):
                return result
        except Exception as e:
            _logger.warning("ai_service.generate_event failed: %s", e)

    return None


def generate_event(
    event_ctx: dict,
    state: dict | None = None,
    ai_service=None,
    prompt: str | None = None,
) -> dict:
    """Generate event narrative using the 4-tier strategy with cascade fallback.

    This is the primary entry point.  It:

    1. Calls :func:`should_use_ai` to determine the tier.
    2. For L1 / L2: returns deterministic, pre-written content.
    3. For L3 / L4: calls the AI service, with cascade fallback on failure:
       **L4 → L3 → L1**  and  **L3 → L1**.

    Args:
        event_ctx: Event context from ``event_engine.build_event_context()``.
        state: Game state dict (for context in L2 and soft cap in tier decision).
        ai_service: ``DeepSeekService`` or compatible instance for AI calls.
        prompt: Pre-built AI prompt string (required for L3 / L4).

    Returns:
        ``dict`` with keys ``narrative``, ``options``, and ``_tier``
        (indicating which tier actually produced the result).
    """
    tier = should_use_ai(event_ctx, state)

    event_type = event_ctx.get("event_type") or event_ctx.get("template", {}).get("type", "daily")
    _logger.debug(
        "event_factory: type=%s tier=%s event_count=%s",
        event_type, tier, state.get("event_count", 0) if state else "n/a",
    )

    if tier == "L1":
        return generate_l1_narrative(event_ctx)

    if tier == "L2":
        return generate_l2_template(event_ctx, state)

    assert tier in ("L3", "L4")

    if prompt is None:
        prompt = event_ctx.get("prompt", "")

    session_id = (state or {}).get("session_id", "")
    count = _ai_call_counts.get(session_id, 0)
    if count >= _AI_CALL_BUDGET_PER_SESSION:
        _logger.info(
            "AI budget exhausted sid=%s count=%d budget=%d → L1 fallback",
            session_id[:8], count, _AI_CALL_BUDGET_PER_SESSION,
        )
        return generate_l1_narrative(event_ctx)

    result = _call_ai_with_fallback(ai_service, prompt, state or {}, tier)
    if result and isinstance(result, dict) and result.get("narrative"):
        result["_tier"] = tier
        if session_id:
            _ai_call_counts[session_id] = count + 1
        return result

    if tier == "L4":
        _logger.info("Cascading L4 → L3 for event type=%s", event_type)
        result = _call_ai_with_fallback(ai_service, prompt, state or {}, "L3")
        if result and isinstance(result, dict) and result.get("narrative"):
            result["_tier"] = "L3"
            if session_id:
                _ai_call_counts[session_id] = _ai_call_counts.get(session_id, 0) + 1
            return result

    _logger.info("Falling back to L1 (rule-based) for event type=%s", event_type)
    return generate_l1_narrative(event_ctx)
