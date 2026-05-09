"""Tag data model system for the event system redesign.

Four tag categories (IDENTITY, SKILL, BOND, STATE) with lifecycle management.
Tags are stored as a JSON blob on PlayerState, not in a separate table.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

MAX_ACTIVE_TAGS = 50


class TagCategory(str, Enum):
    """Four categories of tags, each with a distinct lifecycle strategy.

    IDENTITY: persistent, only event-driven removal (e.g. "青云门弟子", "散修")
    SKILL:    upgrade-driven, new version replaces old (e.g. "剑法入门" -> "剑法精通")
    BOND:     strength-based decay, priority reflects intensity (e.g. "与大师兄交好")
    STATE:    TTL-driven, years_active countdown (e.g. "中毒(5年)", "顿悟中")
    """

    IDENTITY = "identity"
    SKILL = "skill"
    BOND = "bond"
    STATE = "state"


class Tag(BaseModel):
    """A single tag node describing one facet of the character."""

    category: TagCategory
    key: str
    value: str
    description: str = ""
    years_active: int = Field(default=-1)
    priority: int = Field(default=0, ge=0)
    is_active: bool = True

    @property
    def is_persistent(self) -> bool:
        return self.years_active == -1


class TagSet(BaseModel):
    """A curated collection of tags with category-aware lifecycle management.

    Designed to be embedded as a JSON blob field on PlayerState.
    LRU eviction is for in-memory use only; on deserialization the order
    is rebuilt from the current tag list.
    """

    tags: list[Tag] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        self._lru_keys: list[str] = [t.key for t in self.tags]

    def get_by_category(self, category: TagCategory) -> list[Tag]:
        return [t for t in self.tags if t.category == category]

    def get_by_key(self, key: str) -> Tag | None:
        for t in self.tags:
            if t.key == key:
                self._touch(key)
                return t
        return None

    def add(self, tag: Tag) -> None:
        existing = self._find_by_key(tag.key)
        if existing is not None:
            idx = self.tags.index(existing)
            self.tags[idx] = tag
            self._touch(tag.key)
            return

        if len(self.tags) >= MAX_ACTIVE_TAGS:
            self._evict_one_state_tag()

        self.tags.append(tag)
        self._touch(tag.key)

    def remove(self, key: str) -> None:
        self.tags = [t for t in self.tags if t.key != key]
        if key in self._lru_keys:
            self._lru_keys.remove(key)

    def age_tags(self, years: int) -> None:
        expired: list[str] = []
        for tag in self.tags:
            if tag.years_active > 0:
                tag.years_active -= years
                if tag.years_active <= 0:
                    tag.is_active = False
                    expired.append(tag.key)

        for key in expired:
            self.remove(key)

    def to_context_string(self) -> str:
        lines = ["【角色标签】"]

        identity = self.get_by_category(TagCategory.IDENTITY)
        lines.append(f"身份: {self._join_tag_values(identity)}")

        skill = self.get_by_category(TagCategory.SKILL)
        lines.append(f"技能: {self._join_tag_values(skill)}")

        bond = sorted(
            self.get_by_category(TagCategory.BOND),
            key=lambda t: t.priority,
            reverse=True,
        )
        lines.append(f"羁绊: {self._join_tag_values(bond)}")

        state = self.get_by_category(TagCategory.STATE)
        if state:
            parts: list[str] = []
            for t in state:
                if t.years_active > 0:
                    parts.append(f"{t.value}(剩余{t.years_active}年)")
                else:
                    parts.append(t.value)
            lines.append(f"状态: {', '.join(parts)}")
        else:
            lines.append("状态: 无")

        return "\n".join(lines)

    def _find_by_key(self, key: str) -> Tag | None:
        for t in self.tags:
            if t.key == key:
                return t
        return None

    def _touch(self, key: str) -> None:
        if key in self._lru_keys:
            self._lru_keys.remove(key)
        self._lru_keys.append(key)

    def _evict_one_state_tag(self) -> None:
        for key in self._lru_keys:
            tag = self._find_by_key(key)
            if tag is not None and tag.category == TagCategory.STATE:
                self.remove(key)
                return

        state_tags = [t for t in self.tags if t.category == TagCategory.STATE]
        if state_tags:
            self.remove(state_tags[0].key)

    @staticmethod
    def _join_tag_values(tags: list[Tag]) -> str:
        if not tags:
            return "无"
        return ", ".join(t.value for t in tags if t.is_active)
