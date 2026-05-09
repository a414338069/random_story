"""Narrative memory model for AI prompt context injection.

StoryMemory tracks significant life events for the player character.
The StoryMemorySet is embedded as a JSON blob on PlayerState — not a
separate DB table. Memories are used ONLY for AI prompt context, never
for event filtering (trigger_tags are separate).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

MAX_MEMORIES = 20


class StoryMemory(BaseModel):
    """A single narrative memory recording one significant life event.

    Fields:
        event_id: Unique event identifier (e.g. UUID or template_id + timestamp).
        summary: One-line human-readable summary (max 100 chars).
        tags_involved: Tag keys (from TagSystem) that were relevant to this event.
        happened_at_age: Player age when the event occurred.
        emotional_weight: Significance of this memory (0.0 = trivial, 5.0 = unforgettable).
    """

    event_id: str
    summary: str = Field(max_length=100)
    tags_involved: list[str] = Field(default_factory=list)
    happened_at_age: int
    emotional_weight: float = Field(default=1.0, ge=0.0, le=5.0)


class StoryMemorySet(BaseModel):
    """A curated collection of narrative memories for AI prompt injection.

    Automatically enforces MAX_MEMORIES (20). When a new memory is added
    past capacity, the entry with the lowest emotional_weight is evicted.
    Ties are broken by oldest happened_at_age (least recent age first).

    Embedded as a JSON blob on PlayerState — not independently persisted.
    """

    memories: list[StoryMemory] = Field(default_factory=list)

    def add(self, memory: StoryMemory) -> None:
        """Add a memory, evicting the least significant one if over capacity."""
        self.memories.append(memory)

        if len(self.memories) > MAX_MEMORIES:
            self._evict_one()

    def get_recent(self, n: int = 5) -> list[StoryMemory]:
        """Return the n most recent memories sorted by happened_at_age descending."""
        sorted_memories = sorted(
            self.memories,
            key=lambda m: m.happened_at_age,
            reverse=True,
        )
        return sorted_memories[:n]

    def to_prompt_context(self) -> str:
        """Format memories as an AI prompt context block.

        Empty set → returns empty string (no header emitted).

        Output format:
            【过往记忆】
            年龄{age}: {summary}
            年龄{age}: {summary}
            ...
        """
        if not self.memories:
            return ""

        lines = ["【过往记忆】"]
        for m in self.memories:
            lines.append(f"年龄{m.happened_at_age}: {m.summary}")
        return "\n".join(lines)

    def _evict_one(self) -> None:
        """Evict the memory with lowest emotional_weight, oldest age as tiebreaker."""
        target = min(
            self.memories,
            key=lambda m: (m.emotional_weight, m.happened_at_age),
        )
        self.memories.remove(target)
