from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.sql import func

from database import Base


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, nullable=False, index=True)
    owner_name = Column(String, nullable=True)          # None = данных нет
    rating = Column(Float, nullable=True, default=None)
    votes = Column(Integer, default=0, nullable=False)
    warning = Column(Text, nullable=True)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, nullable=False, index=True)
    text = Column(Text, nullable=False)
    rating = Column(Float, nullable=False)               # раз в CarResponse None — значит без отзывов
    is_anonymous = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)