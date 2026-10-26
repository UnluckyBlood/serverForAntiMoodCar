from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class CarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    found: bool
    plate_number: str
    owner_name: str
    rating: Optional[float] = None
    votes: int = 0
    warning: Optional[str] = None


class ReviewCreate(BaseModel):
    text: str
    rating: float
    is_anonymous: bool = True

    @field_validator("rating")
    @classmethod
    def check_rating(cls, v: float) -> float:
        if not (1 <= v <= 5):
            raise ValueError("Рейтинг должен быть от 1 до 5")
        return v


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plate_number: str
    text: str
    rating: Optional[float] = None
    is_anonymous: bool
    created_at: datetime