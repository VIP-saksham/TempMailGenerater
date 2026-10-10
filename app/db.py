import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

db_url = settings.database_url
if db_url.startswith("sqlite:///./"):
    # ensure parent dir exists when db path is relative
    parent = os.path.dirname(db_url.replace("sqlite:///./", "", 1))
    if parent:
        os.makedirs(parent, exist_ok=True)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
