from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models import Base

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()