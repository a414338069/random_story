"""Game lifecycle Pydantic v2 schemas."""

from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field, StringConstraints

from app.models.player import Attributes, PlayerState


class GameStartRequest(BaseModel):
    """Request body for starting a new game."""

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10)]
    gender: Literal["男", "女"]
    talent_card_ids: list[str] = Field(min_length=3, max_length=3)
    attributes: Attributes
    user_id: Optional[str] = None
    save_slot: Optional[int] = None


class GameStartResponse(BaseModel):
    """Response after a new game is started."""

    session_id: str
    state: PlayerState


class GameEndResponse(BaseModel):
    """Response when a game session ends."""

    session_id: str
    final_state: PlayerState
    reason: str = ""


class EndGameRequest(BaseModel):
    """Request body for ending a game session."""

    session_id: str


class LeaderboardEntry(BaseModel):
    """A single entry on the leaderboard."""

    rank: int = Field(ge=1)
    player_name: str
    score: int
    realm: str
    ending_id: Optional[str] = None
