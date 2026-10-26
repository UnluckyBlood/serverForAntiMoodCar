from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, engine
from models import Base, Car, Review
from schemas import CarResponse, ReviewCreate, ReviewOut
from typing import List

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def update_car_rating(db: Session, plate: str):
    plate = plate.upper()
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.plate_number == plate).scalar()
    votes = db.query(Review).filter(Review.plate_number == plate).count()

    car = db.query(Car).filter(Car.plate_number == plate).first()
    if car:
        if avg_rating is not None:
            car.rating = round(float(avg_rating), 2)
            car.votes = votes
        else:
            car.rating = None
            car.votes = 0
        db.commit()


def get_or_create_car(db: Session, plate: str) -> Car:
    plate = plate.upper()
    car = db.query(Car).filter(Car.plate_number == plate).first()
    if not car:
        car = Car(
            plate_number=plate,
            owner_name="ещё нет данных",
            rating=None,          # нет оценок
            votes=0,
            warning="Об пользователе нет данных"
        )
        db.add(car)
        db.commit()
        db.refresh(car)
    return car


@app.get("/")
def root():
    return {"message": "AutoMooden API работает"}


@app.get("/api/car/{plate}", response_model=CarResponse)
def get_car(plate: str, db: Session = Depends(get_db)):
    car = get_or_create_car(db, plate)
    return {
        "found": True,
        "plate_number": car.plate_number,
        "owner_name": car.owner_name,
        "rating": car.rating,      # может быть None
        "votes": car.votes,
        "warning": car.warning
    }


@app.get("/api/reviews/{plate}", response_model=List[ReviewOut])
def get_reviews(plate: str, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(
        Review.plate_number == plate.upper()
    ).order_by(Review.created_at.desc()).all()
    return reviews


@app.post("/api/reviews/{plate}", response_model=ReviewOut)
def create_review(plate: str, review: ReviewCreate, db: Session = Depends(get_db)):
    car = get_or_create_car(db, plate)
    db_review = Review(
        plate_number=plate.upper(),
        text=review.text,
        rating=review.rating,
        is_anonymous=True
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    update_car_rating(db, plate)
    return db_review


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)