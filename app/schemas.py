"""Request/response schemas, kept separate from the DB table models."""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---- Certifications -------------------------------------------------

class CertificationCreate(BaseModel):
    name: str = Field(..., min_length=1, examples=["AZ-900"])
    target_hours: float = Field(default=20.0, gt=0)
    exam_date: Optional[date] = None


class CertificationUpdate(BaseModel):
    target_hours: Optional[float] = Field(default=None, gt=0)
    exam_date: Optional[date] = None


class CertificationRead(BaseModel):
    id: int
    name: str
    target_hours: float
    exam_date: Optional[date]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReadinessBreakdown(BaseModel):
    cert_id: int
    cert_name: str
    readiness_score: float = Field(..., description="0-100 composite readiness score.")
    hours_logged: float
    target_hours: float
    hours_progress_pct: float = Field(..., description="hours_logged / target_hours, capped at 100.")
    average_confidence: Optional[float] = Field(None, description="Mean self-rated confidence across sessions.")
    session_count: int
    exam_date: Optional[date]


# ---- Study sessions -----------------------------------------------------

class StudySessionCreate(BaseModel):
    # Either cert_id (existing cert) or cert_name (looked up, auto-created
    # with default target_hours if it doesn't exist yet) may be supplied.
    cert_id: Optional[int] = None
    cert_name: Optional[str] = Field(default=None, examples=["AZ-900"])
    session_date: date = Field(default_factory=date.today)
    hours: float = Field(..., gt=0)
    topic: str = Field(..., min_length=1)
    confidence: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None


class StudySessionRead(BaseModel):
    id: int
    cert_id: int
    session_date: date
    hours: float
    topic: str
    confidence: int
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NextUpResponse(BaseModel):
    cert: ReadinessBreakdown
    reason: str


class AllReadinessResponse(BaseModel):
    certifications: List[ReadinessBreakdown]