"""Event-related Pydantic v2 schemas."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class EventOption(BaseModel):
    """A single option presented to the player."""

    id: str
    text: str
    consequence_preview: Optional[str] = None


class EventResponse(BaseModel):
    """AI-generated event with narrative and options."""

    narrative: str
    options: list[EventOption] = Field(default_factory=list)
    has_options: bool = True
    title: Optional[str] = None
    metadata: Optional[dict] = None
    is_breakthrough: bool = False

    @field_validator("narrative")
    @classmethod
    def validate_narrative_length(cls, v: str) -> str:
        if len(v) < 20:
            raise ValueError(f"叙事文本长度不能少于20字，当前为{len(v)}字")
        if len(v) > 500:
            raise ValueError(f"叙事文本长度不能超过500字，当前为{len(v)}字")
        return v


class EventRequest(BaseModel):
    """Request to generate a new event for a player."""

    player_id: str
    current_realm: str = ""
    event_count: int = Field(default=0, ge=0)


class EventChooseRequest(BaseModel):
    """Request when a player chooses an event option."""

    player_id: str
    event_id: str
    option_id: str


class ChooseRequest(BaseModel):
    """Request to choose an option in a current event."""

    session_id: str
    option_id: Optional[str] = None


class BreakthroughInfo(BaseModel):
    """Breakthrough information returned after a choice."""
    message: str
    new_realm: Optional[str] = None
    success: Optional[bool] = None
    use_pill: bool | None = None


class AftermathResponse(BaseModel):
    """Consequence information after a player choice."""
    cultivation_change: float = 0.0
    age_advance: int = 0
    narrative: Optional[str] = None
    breakthrough: Optional[BreakthroughInfo] = None


class ChooseResponse(BaseModel):
    """Structured response for /event/choose endpoint."""
    state: dict
    aftermath: AftermathResponse
