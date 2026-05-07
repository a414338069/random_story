"""Save system Pydantic v2 schemas."""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.player import PlayerState


class SaveSlotInfo(BaseModel):
    """Summary of a single save slot."""

    slot: int
    session_id: str
    name: str
    realm: str
    age: int
    event_count: int
    last_active_at: Optional[str] = None
    is_alive: bool = True


class SaveListResponse(BaseModel):
    """Response listing all save slots for a user."""

    saves: list[SaveSlotInfo]


class SaveLoadRequest(BaseModel):
    """Request body for loading a save."""

    user_id: str
    save_slot: int


class SaveLoadResponse(BaseModel):
    """Response after loading a save — full session state."""

    session_id: str
    state: PlayerState


class SaveDeleteRequest(BaseModel):
    """Request body for deleting a save (also usable as path-param alternative)."""

    user_id: str
    save_slot: int
