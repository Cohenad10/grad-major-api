from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection for your SurveyData DB
DATABASE_URL = "postgresql://postgres:Mustang@localhost:5432/SurveyData"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
