from enum import Enum


class LifeStage(Enum):
    INFANT = "infant"
    CHILD = "child"
    YOUTH = "youth"
    CULTIVATOR = "cultivator"


def get_life_stage(age: int) -> LifeStage:
    if age <= 3:
        return LifeStage.INFANT
    if age <= 11:
        return LifeStage.CHILD
    if age <= 15:
        return LifeStage.YOUTH
    return LifeStage.CULTIVATOR


def get_cultivation_multiplier(age: int) -> float:
    stage = get_life_stage(age)
    if stage in (LifeStage.INFANT, LifeStage.CHILD):
        return 0.0
    if stage == LifeStage.YOUTH:
        return 0.5
    return 1.0


def can_attempt_breakthrough(age: int) -> bool:
    return age >= 16


def get_breakthrough_penalty(age: int) -> float:
    if age < 16:
        return 0.5
    return 0.0
