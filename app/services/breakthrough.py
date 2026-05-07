import random
from dataclasses import dataclass

from app.services.realm_service import get_realm_config, get_next_realm, load_realms
from app.services.talent_service import load_talents
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


def calculate_success_rate(player_state: dict, use_pill: bool = False) -> float:
    root_bone = player_state.get("rootBone", 0)
    comprehension = player_state.get("comprehension", 0)
    mindset = player_state.get("mindset", 0)
    realm = player_state.get("realm", "凡人")
    age = player_state.get("age", 16)  # 默认 16（突破最低年龄）

    penalty = get_realm_penalty(realm)
    rate = 0.50 + root_bone * 0.05 + comprehension * 0.03 + mindset * 0.02 - penalty

    if use_pill:
        rate += PILL_BONUS

    # 年龄惩罚
    age_penalty = get_breakthrough_penalty(age)
    rate *= (1 - age_penalty)

    return max(0.05, min(0.95, rate))


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


def attempt_breakthrough(player_state: dict, use_pill: bool = False) -> BreakthroughResult:
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

    rate = calculate_success_rate(player_state, use_pill)
    success = random.random() < rate

    if success:
        ascended = next_realm == "渡劫飞升"
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
