# database.py
# SQLAlchemy engine and session factory.
# All other modules import `get_db` (a FastAPI dependency) to access a DB session.
# Swapping the database engine only requires changing DATABASE_URL in config.py.

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

# connect_args is only needed for SQLite (disables same-thread check)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and closes it when the request ends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
