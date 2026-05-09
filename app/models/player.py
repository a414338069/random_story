"""Player-related Pydantic v2 schemas."""

from typing import Optional
from pydantic import BaseModel, Field, model_validator


class Attributes(BaseModel):
    """Player base attributes. Each field 0-10, sum must be exactly 10."""

    root_bone: int = Field(default=0, ge=0, le=10, description="根骨")
    comprehension: int = Field(default=0, ge=0, le=10, description="悟性")
    mindset: int = Field(default=0, ge=0, le=10, description="心境")
    luck: int = Field(default=0, ge=0, le=10, description="气运")

    @model_validator(mode="after")
    def validate_sum(self) -> "Attributes":
        total = self.root_bone + self.comprehension + self.mindset + self.luck
        if total != 10:
            raise ValueError(f"四维属性总和必须为10，当前为{total}")
        return self


class Technique(BaseModel):
    """A technique/skill the player has learned."""

    id: str
    name: str
    description: str = ""
    modifier: float = Field(default=1.0, ge=0.0, description="修为获取倍率")


class InventoryItem(BaseModel):
    """An item in the player's inventory."""

    id: str
    name: str
    quantity: int = Field(default=1, ge=1)


class SectInfo(BaseModel):
    """Player's sect/faction affiliation."""

    faction: str = ""
    rank: str = ""


class PlayerState(BaseModel):
    """Full player state, corresponding to the `players` table schema."""

    id: str
    name: str
    gender: str = ""
    talent_ids: list[str] = Field(default_factory=list)

    root_bone: int = Field(default=0, ge=0, le=10)
    comprehension: int = Field(default=0, ge=0, le=10)
    mindset: int = Field(default=0, ge=0, le=10)
    luck: int = Field(default=0, ge=0, le=10)

    realm: str = ""
    realm_progress: float = Field(default=0.0, ge=0.0)
    cultivation: float = Field(default=0.0, ge=0.0)
    age: int = Field(default=0, ge=0)

    health: float = Field(default=100.0, ge=0.0)
    qi: float = Field(default=0.0, ge=0.0)
    lifespan: int = Field(default=100, ge=0)

    faction: str = ""
    spirit_stones: int = Field(default=0, ge=0)
    techniques: list[str] = Field(default_factory=list)
    inventory: list[str] = Field(default_factory=list)
    event_count: int = Field(default=0, ge=0)
    score: int = Field(default=0)

    technique_grades: list[str] = Field(default_factory=list)
    ascended: bool = False

    ending_id: Optional[str] = None
    is_alive: bool = True

    last_active_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    tags_json: Optional[str] = None
    story_memory_json: Optional[str] = None
