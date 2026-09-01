"""Database access helpers, kept separate from the route handlers."""
from typing import List, Optional

from sqlmodel import Session, select

from . import scoring
from .models import Certification, StudySession
from .schemas import CertificationCreate, CertificationUpdate, ReadinessBreakdown, StudySessionCreate


# ---- Certifications ---------------------------------------------------

def create_certification(session: Session, data: CertificationCreate) -> Certification:
    existing = session.exec(select(Certification).where(Certification.name == data.name)).first()
    if existing:
        raise ValueError(f"Certification '{data.name}' already exists (id={existing.id}).")
    cert = Certification(name=data.name, target_hours=data.target_hours, exam_date=data.exam_date)
    session.add(cert)
    session.commit()
    session.refresh(cert)
    return cert


def get_certification(session: Session, cert_id: int) -> Optional[Certification]:
    return session.get(Certification, cert_id)


def get_certification_by_name(session: Session, name: str) -> Optional[Certification]:
    return session.exec(select(Certification).where(Certification.name == name)).first()


def get_or_create_certification_by_name(
    session: Session, name: str, default_target_hours: float = 20.0
) -> Certification:
    cert = get_certification_by_name(session, name)
    if cert:
        return cert
    cert = Certification(name=name, target_hours=default_target_hours)
    session.add(cert)
    session.commit()
    session.refresh(cert)
    return cert


def list_certifications(session: Session) -> List[Certification]:
    return list(session.exec(select(Certification).order_by(Certification.name)))


def update_certification(session: Session, cert: Certification, data: CertificationUpdate) -> Certification:
    if data.target_hours is not None:
        cert.target_hours = data.target_hours
    if data.exam_date is not None:
        cert.exam_date = data.exam_date
    session.add(cert)
    session.commit()
    session.refresh(cert)
    return cert


def delete_certification(session: Session, cert: Certification) -> None:
    session.delete(cert)
    session.commit()


# ---- Study sessions -----------------------------------------------------

def create_study_session(session: Session, data: StudySessionCreate) -> StudySession:
    if data.cert_id is not None:
        cert = get_certification(session, data.cert_id)
        if cert is None:
            raise ValueError(f"No certification with id={data.cert_id}.")
    elif data.cert_name:
        cert = get_or_create_certification_by_name(session, data.cert_name)
    else:
        raise ValueError("Provide either cert_id or cert_name.")

    study_session = StudySession(
        cert_id=cert.id,
        session_date=data.session_date,
        hours=data.hours,
        topic=data.topic,
        confidence=data.confidence,
        notes=data.notes,
    )
    session.add(study_session)
    session.commit()
    session.refresh(study_session)
    return study_session


def list_study_sessions(session: Session, cert_id: Optional[int] = None) -> List[StudySession]:
    query = select(StudySession).order_by(StudySession.session_date.desc())
    if cert_id is not None:
        query = query.where(StudySession.cert_id == cert_id)
    return list(session.exec(query))


# ---- Readiness ----------------------------------------------------------

def readiness_for_cert(session: Session, cert: Certification) -> ReadinessBreakdown:
    sessions = list_study_sessions(session, cert_id=cert.id)
    hours_logged = round(sum(s.hours for s in sessions), 2)
    confidences = [s.confidence for s in sessions]

    return ReadinessBreakdown(
        cert_id=cert.id,
        cert_name=cert.name,
        readiness_score=scoring.readiness_score(hours_logged, cert.target_hours, confidences),
        hours_logged=hours_logged,
        target_hours=cert.target_hours,
        hours_progress_pct=scoring.hours_progress_pct(hours_logged, cert.target_hours),
        average_confidence=scoring.average_confidence(confidences),
        session_count=len(sessions),
        exam_date=cert.exam_date,
    )


def readiness_for_all(session: Session) -> List[ReadinessBreakdown]:
    return [readiness_for_cert(session, cert) for cert in list_certifications(session)]