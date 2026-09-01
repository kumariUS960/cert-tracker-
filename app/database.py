"""Database engine + session setup for Cert Tracker.

Uses SQLite via SQLModel (SQLAlchemy + Pydantic) so the whole project
runs with zero external services -- just `pip install` and go.
"""
import os
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

# Overridable via env var so tests can point at a throwaway DB file.
DATABASE_URL = os.environ.get("CERT_TRACKER_DB_URL", "sqlite:///./cert_tracker.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Create tables if they don't already exist."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a DB session per-request."""
    with Session(engine) as session:
        yield session