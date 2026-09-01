"""Cert Tracker API.

Run it with:
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.
"""
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session

from . import crud
from .database import get_session, init_db
from .schemas import (
    AllReadinessResponse,
    CertificationCreate,
    CertificationRead,
    CertificationUpdate,
    NextUpResponse,
    ReadinessBreakdown,
    StudySessionCreate,
    StudySessionRead,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Cert Tracker",
    description="Track study sessions across multiple certifications and see what to study next.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": "cert-tracker",
        "docs": "/docs",
        "endpoints": ["/certs", "/sessions", "/readiness", "/next"],
    }


# ---- Certifications -------------------------------------------------

@app.post("/certs", response_model=CertificationRead, status_code=201, tags=["certifications"])
def create_certification(data: CertificationCreate, session: Session = Depends(get_session)):
    try:
        return crud.create_certification(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/certs", response_model=List[CertificationRead], tags=["certifications"])
def list_certifications(session: Session = Depends(get_session)):
    return crud.list_certifications(session)


@app.get("/certs/{cert_id}", response_model=CertificationRead, tags=["certifications"])
def get_certification(cert_id: int, session: Session = Depends(get_session)):
    cert = crud.get_certification(session, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail=f"No certification with id={cert_id}.")
    return cert


@app.patch("/certs/{cert_id}", response_model=CertificationRead, tags=["certifications"])
def update_certification(cert_id: int, data: CertificationUpdate, session: Session = Depends(get_session)):
    cert = crud.get_certification(session, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail=f"No certification with id={cert_id}.")
    return crud.update_certification(session, cert, data)


@app.delete("/certs/{cert_id}", status_code=204, tags=["certifications"])
def delete_certification(cert_id: int, session: Session = Depends(get_session)):
    cert = crud.get_certification(session, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail=f"No certification with id={cert_id}.")
    crud.delete_certification(session, cert)


# ---- Study sessions -----------------------------------------------------

@app.post("/sessions", response_model=StudySessionRead, status_code=201, tags=["sessions"])
def log_study_session(data: StudySessionCreate, session: Session = Depends(get_session)):
    """Log a study session. Pass either `cert_id` (existing cert) or
    `cert_name` (auto-creates the cert with a default 20h target if new)."""
    try:
        return crud.create_study_session(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/sessions", response_model=List[StudySessionRead], tags=["sessions"])
def list_study_sessions(cert_id: Optional[int] = None, session: Session = Depends(get_session)):
    return crud.list_study_sessions(session, cert_id=cert_id)


# ---- Readiness ------------------------------------------------------------

@app.get("/certs/{cert_id}/readiness", response_model=ReadinessBreakdown, tags=["readiness"])
def get_cert_readiness(cert_id: int, session: Session = Depends(get_session)):
    cert = crud.get_certification(session, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail=f"No certification with id={cert_id}.")
    return crud.readiness_for_cert(session, cert)


@app.get("/readiness", response_model=AllReadinessResponse, tags=["readiness"])
def get_all_readiness(session: Session = Depends(get_session)):
    return AllReadinessResponse(certifications=crud.readiness_for_all(session))


@app.get("/next", response_model=NextUpResponse, tags=["readiness"])
def what_to_study_next(session: Session = Depends(get_session)):
    """Returns whichever tracked certification currently has the lowest
    readiness score -- ties broken by name for stable output."""
    breakdowns = crud.readiness_for_all(session)
    if not breakdowns:
        raise HTTPException(status_code=404, detail="No certifications tracked yet. POST /certs to add one.")

    lowest = min(breakdowns, key=lambda b: (b.readiness_score, b.cert_name))
    return NextUpResponse(
        cert=lowest,
        reason=(
            f"'{lowest.cert_name}' has the lowest readiness score "
            f"({lowest.readiness_score}/100) among {len(breakdowns)} tracked cert(s)."
        ),
    )