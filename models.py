from sqlalchemy import Column, Integer, String, Boolean, Float, TIMESTAMP
from sqlalchemy.sql import func

from database import Base


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)

    # Section 1
    q1 = Column(Integer)
    q2 = Column(Integer)
    q3 = Column(String)
    q4 = Column(Integer)
    q5 = Column(String)

    # Section 2
    q6 = Column(Integer)
    q7 = Column(String)
    q8 = Column(Integer)
    q9 = Column(Boolean)
    q10 = Column(Integer)

    # Section 3
    q11 = Column(Integer)
    q12 = Column(Integer)
    q13 = Column(Integer)
    q14 = Column(Integer)
    q15 = Column(Integer)

    # Section 4 — RIASEC personality items
    r1 = Column(Integer)
    i1 = Column(Integer)
    a1 = Column(Integer)
    s1 = Column(Integer)
    e1 = Column(Integer)
    c1 = Column(Integer)

    submitted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    soc_code = Column(String, index=True)
    title = Column(String)
    description = Column(String)
    focus_area = Column(String)  # 'data analysis', 'systems management', etc.

    required_data_skill = Column(Integer)
    required_tech_interest = Column(Integer)
    required_communication = Column(Integer)
    stability_level = Column(Integer)
    salary_level = Column(Integer)
    remote_possible = Column(Boolean)

    job_zone = Column(Integer)

    # RIASEC interest scores from O*NET
    riasec_r = Column(Float)
    riasec_i = Column(Float)
    riasec_a = Column(Float)
    riasec_s = Column(Float)
    riasec_e = Column(Float)
    riasec_c = Column(Float)
