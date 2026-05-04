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
    options: list[EventOption] = Field(min_length=2, max_length=3)
    metadata: Optional[dict] = None

    @field_validator("narrative")
    @classmethod
    def validate_narrative_length(cls, v: str) -> str:
        if len(v) < 20:
            raise ValueError(f"叙事文本长度不能少于20字，当前为{len(v)}字")
        if len(v) > 500:
            raise ValueError(f"叙事文本长度不能超过500字，当前为{len(v)}字")
        return v

    @field_validator("options")
    @classmethod
    def validate_options_count(cls, v: list[EventOption]) -> list[EventOption]:
        if len(v) < 2 or len(v) > 3:
            raise ValueError(f"选项数量必须为2-3个，当前为{len(v)}个")
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
    option_id: str
