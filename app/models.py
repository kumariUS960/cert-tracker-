"""SQLModel table definitions.

Two tables:
  * Certification  -- one row per cert you're pursuing (AZ-900, DP-900, ...)
  * StudySession   -- one row per study session logged against a cert
"""
from datetime import date, datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Certification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, description="e.g. 'AZ-900'")
    target_hours: float = Field(
        default=20.0,
        gt=0,
        description="Estimated hours of study needed to feel exam-ready.",
    )
    exam_date: Optional[date] = Field(default=None, description="Scheduled exam date, if booked.")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    sessions: List["StudySession"] = Relationship(
        back_populates="certification",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class StudySession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cert_id: int = Field(foreign_key="certification.id", index=True)
    session_date: date = Field(default_factory=date.today)
    hours: float = Field(gt=0, description="Hours spent in this session.")
    topic: str = Field(description="What you studied, e.g. 'Azure networking basics'.")
    confidence: int = Field(ge=1, le=5, description="Self-rated confidence, 1 (shaky) to 5 (solid).")
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    certification: Optional[Certification] = Relationship(back_populates="sessions")