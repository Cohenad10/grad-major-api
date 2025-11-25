from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
from schemas import SurveySchema
from models import SurveyResponse
from recommendation import generate_recommendation

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/submit")
def submit_survey(data: SurveySchema, db: Session = Depends(get_db)):
    # Save survey response
    db_entry = SurveyResponse(**data.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    # Generate recommendations (major + top jobs)
    rec = generate_recommendation(data, db, top_n=5)

    return {
        "status": "success",
        "recommended_major": rec["recommended_major"],
        "top_jobs": rec["top_jobs"],
        "data_id": db_entry.id,
    }
