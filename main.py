import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal, engine
from models import Base, Car, Review
from schemas import CarResponse, ReviewCreate, ReviewOut

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AutoMooden API")

# CORS нужен только если будете открывать /docs из браузера.
# На работу Android он не влияет.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NO_DATA = "О пользователе нет данных"   # ← грамматика: "О", а не "Об"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_or_create_car(db: Session, plate: str) -> Car:
    plate = plate.upper()
    car = db.query(Car).filter(Car.plate_number == plate).first()
    if car:
        return car
    car = Car(plate_number=plate, owner_name=None, rating=None, votes=0, warning=None)
    db.add(car)
    try:
        db.commit()
    except IntegrityError:
        # кто-то успел вставить параллельно — просто достаём
        db.rollback()
        return db.query(Car).filter(Car.plate_number == plate).one()
    db.refresh(car)
    return car


def _update_car_rating(db: Session, plate: str) -> None:
    plate = plate.upper()
    # блокируем строку, чтобы два одновременных POST не разъехались
    car = db.query(Car).filter(Car.plate_number == plate).with_for_update().first()
    if not car:
        return
    avg_rating = (
        db.query(func.avg(Review.rating))
        .filter(Review.plate_number == plate)
        .scalar()
    )
    votes = db.query(Review).filter(Review.plate_number == plate).count()
    car.rating = round(float(avg_rating), 2) if avg_rating is not None else None
    car.votes = votes
    db.commit()


@app.get("/")
def root():
    return {"message": "AutoMooden API работает"}


@app.get("/api/car/{plate}", response_model=CarResponse)
def get_car(plate: str, db: Session = Depends(get_db)):
    plate = plate.upper()
    car = db.query(Car).filter(Car.plate_number == plate).first()

    # found=False — номера ещё нет в базе (но его можно создать через POST /reviews).
    # Если ваш Android-клиент ожидает всегда found=True — замените на _get_or_create_car.
    if car is None:
        return CarResponse(
            found=False,
            plate_number=plate,
            owner_name=NO_DATA,
            rating=None,
            votes=0,
            warning=NO_DATA,
        )

    return CarResponse(
        found=True,
        plate_number=car.plate_number,
        owner_name=car.owner_name or NO_DATA,
        rating=car.rating,
        votes=car.votes,
        warning=car.warning or (NO_DATA if car.owner_name is None else None),
    )


@app.get("/api/reviews/{plate}", response_model=List[ReviewOut])
def get_reviews(plate: str, db: Session = Depends(get_db)):
    return (
        db.query(Review)
        .filter(Review.plate_number == plate.upper())
        .order_by(Review.created_at.desc())
        .all()
    )


@app.post("/api/reviews/{plate}", response_model=ReviewOut)
def create_review(plate: str, review: ReviewCreate, db: Session = Depends(get_db)):
    _get_or_create_car(db, plate)
    db_review = Review(
        plate_number=plate.upper(),
        text=review.text,
        rating=review.rating,
        is_anonymous=review.is_anonymous,
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    _update_car_rating(db, plate)
    return db_review


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),      # слушать все интерфейсы — важно для Android
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
    )