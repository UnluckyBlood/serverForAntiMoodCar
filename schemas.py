from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

class CarResponse(BaseModel):
    found: bool
    plate_number: str
    owner_name: str
    rating: Optional[float] = None
    votes: int = 0
    warning: Optional[str] = None

    class Config:
        from_attributes = True

class ReviewCreate(BaseModel):
    text: str
    rating: float

    @field_validator('rating')
    @classmethod
    def check_rating(cls, v):
        if not (1 <= v <= 5):
            raise ValueError('Рейтинг должен быть от 1 до 5')
        return v

class ReviewOut(BaseModel):
    id: int
    plate_number: str
    text: str
    rating: Optional[float] = None
    is_anonymous: bool
    created_at: datetime

    class Config:
        from_attributes = True