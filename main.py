from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from routes.survey import router as survey_router
from models import SurveyResponse, Job

app = FastAPI(title="Graduate Major Recommendation API")

# Create tables for SurveyResponse (jobs table already exists)
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(survey_router)

# Static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates (for admin dashboard)
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", include_in_schema=False)
def read_root():
    # Serve the main survey UI
    return FileResponse("static/survey.html")


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    total_surveys = db.query(SurveyResponse).count()
    total_jobs = db.query(Job).count()
    recent = (
        db.query(SurveyResponse)
        .order_by(SurveyResponse.submitted_at.desc())
        .limit(20)
        .all()
    )
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "total_surveys": total_surveys,
            "total_jobs": total_jobs,
            "recent_surveys": recent,
        },
    )
