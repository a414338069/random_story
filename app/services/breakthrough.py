from __future__ import annotations

import random
from dataclasses import dataclass

from app.models.tags import Tag, TagCategory, TagSet
from app.services.realm_service import get_realm_config, get_next_realm, load_realms
from app.services.talent_service import get_active_modifiers, has_talent_effect, load_talents
from app.services.life_stage import get_breakthrough_penalty

REALM_PENALTY = {
    "凡人": 0.0,
    "炼气": 0.05,
    "筑基": 0.10,
    "金丹": 0.15,
    "元婴": 0.20,
    "化神": 0.25,
    "合体": 0.30,
    "大乘": 0.35,
}

BULWARK_TALENT_NAME = "百折不挠"
BULWARK_LOSS_REDUCTION = 0.10
PILL_BONUS = 0.15


@dataclass
class BreakthroughResult:
    success: bool
    new_realm: str
    cultivation_loss: float
    realm_dropped: bool
    ascended: bool


def get_realm_penalty(current_realm: str) -> float:
    return REALM_PENALTY.get(current_realm, 0.0)


def calculate_success_rate(
    player_state: dict,
    use_pill: bool = False,
    tags: TagSet | None = None,
    talent_ids: list[str] | None = None,
) -> float:
    root_bone = player_state.get("rootBone", 0)
    comprehension = player_state.get("comprehension", 0)
    mindset = player_state.get("mindset", 0)
    realm = player_state.get("realm", "凡人")
    age = player_state.get("age", 16)  # 默认 16（突破最低年龄）

    penalty = get_realm_penalty(realm)
    rate = 0.50 + root_bone * 0.05 + comprehension * 0.03 + mindset * 0.02 - penalty

    if use_pill:
        rate += PILL_BONUS

    # Talent-enhanced pill effect (e.g., 血祭之契 l06)
    if use_pill and talent_ids and has_talent_effect(talent_ids, "breakthrough_pill_chance"):
        rate += 0.25

    # Tag-based modifiers
    if tags:
        # Master bond: +5% success rate
        master = tags.get_by_key("bond_master")
        if master:
            rate += 0.05

        # Blessed state: +3% success rate (temporary)
        blessed = tags.get_by_key("state_blessed")
        if blessed and blessed.is_active:
            rate += 0.03

        # Injured state: -10% success rate
        injured = tags.get_by_key("state_injured")
        if injured and injured.is_active:
            rate -= 0.10

    # 年龄惩罚
    age_penalty = get_breakthrough_penalty(age)
    rate *= (1 - age_penalty)

    # 天赋突破率加成
    if talent_ids:
        modifiers = get_active_modifiers(talent_ids)
        rate += modifiers.get("breakthrough_rate_bonus", 0.0)

    return max(0.05, min(1.0, rate))


def _get_prev_realm(current: str) -> str | None:
    config = get_realm_config(current)
    if config is None:
        return None
    prev_order = config["order"] - 1
    if prev_order < 1:
        return None
    realms = load_realms()
    for r in realms:
        if r["order"] == prev_order:
            return r["name"]
    return None


def _has_talent(player_state: dict, talent_name: str) -> bool:
    talents = load_talents()
    talent_map = {t["name"]: t["id"] for t in talents}
    talent_id = talent_map.get(talent_name)
    if talent_id is None:
        return False
    return talent_id in player_state.get("talent_ids", [])


def attempt_breakthrough(
    player_state: dict,
    use_pill: bool = False,
    tags: TagSet | None = None,
) -> BreakthroughResult:
    realm = player_state.get("realm", "凡人")
    cultivation = player_state.get("cultivation", 0)

    next_realm = get_next_realm(realm)
    if next_realm is None:
        return BreakthroughResult(
            success=True,
            new_realm=realm,
            cultivation_loss=0.0,
            realm_dropped=False,
            ascended=True,
        )

    talent_ids = player_state.get("talent_ids", [])
    rate = calculate_success_rate(player_state, use_pill, tags=tags, talent_ids=talent_ids)
    success = random.random() < rate

    if success:
        ascended = next_realm == "渡劫飞升"

        # l06 血祭之契 negative effect: 突破成功后以30%气血为代价
        if success and use_pill and has_talent_effect(talent_ids, "breakthrough_health_cost"):
            current_hp = player_state.get("current_health", player_state.get("max_health", 100))
            health_cost = current_hp * 0.3
            player_state["current_health"] = max(1, int(current_hp - health_cost))

        if tags:
            tags.add(Tag(
                category=TagCategory.STATE,
                key="realm_current",
                value=f"境界={next_realm}",
                description=f"当前修炼境界: {next_realm}",
            ))

        return BreakthroughResult(
            success=True,
            new_realm=next_realm,
            cultivation_loss=0.0,
            realm_dropped=False,
            ascended=ascended,
        )

    loss_ratio = random.uniform(0.20, 0.50)

    if _has_talent(player_state, BULWARK_TALENT_NAME):
        loss_ratio = max(0.0, loss_ratio - BULWARK_LOSS_REDUCTION)

    cultivation_loss = cultivation * loss_ratio

    realm_drop_roll = random.random()
    if realm_drop_roll < 0.10:
        prev = _get_prev_realm(realm)
        if prev is not None:
            return BreakthroughResult(
                success=False,
                new_realm=prev,
                cultivation_loss=cultivation_loss,
                realm_dropped=True,
                ascended=False,
            )

    return BreakthroughResult(
        success=False,
        new_realm=realm,
        cultivation_loss=cultivation_loss,
        realm_dropped=False,
        ascended=False,
    )


def build_breakthrough_event(player_state: dict) -> dict:
    inventory = player_state.get("inventory", [])
    has_pill = "breakthrough_pill" in inventory

    options = []
    if has_pill:
        options.append(
            {"id": "use_pill", "text": "服用突破丹（成功率 +15%）", "consequence_preview": None}
        )
    options.append(
        {"id": "direct", "text": "凭自身实力突破", "consequence_preview": None}
    )

    return {
        "event_id": "breakthrough_pending",
        "title": "境界突破",
        "narrative": "你的修为已达瓶颈，丹田中灵力如潮水般涌动，周身经脉隐隐作痛。一道无形的屏障横亘在前，这是通往下一境界的壁障。",
        "options": options,
        "is_breakthrough": True,
        "has_options": True,
    }
