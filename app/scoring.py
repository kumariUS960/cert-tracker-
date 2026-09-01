"""Readiness score calculation.

Kept as pure functions (no DB, no FastAPI) so they're trivial to unit test
in isolation from the API layer.

Formula
-------
readiness = hours_component + confidence_component

    hours_component      = min(hours_logged / target_hours, 1.0) * HOURS_WEIGHT
    confidence_component = (average_confidence / 5) * CONFIDENCE_WEIGHT

With HOURS_WEIGHT=60 and CONFIDENCE_WEIGHT=40, a cert only reaches 100 when
you've both put in the target hours *and* rate yourself confident on what
you covered -- logging hours alone caps out at 60, and confidence alone
caps out at 40.

A cert with zero logged sessions always scores 0.
"""
from typing import Optional, Sequence

HOURS_WEIGHT = 60.0
CONFIDENCE_WEIGHT = 40.0
MAX_CONFIDENCE = 5.0


def hours_progress_pct(hours_logged: float, target_hours: float) -> float:
    if target_hours <= 0:
        return 0.0
    return round(min(hours_logged / target_hours, 1.0) * 100, 1)


def average_confidence(confidences: Sequence[int]) -> Optional[float]:
    if not confidences:
        return None
    return round(sum(confidences) / len(confidences), 2)


def readiness_score(hours_logged: float, target_hours: float, confidences: Sequence[int]) -> float:
    if not confidences:
        return 0.0

    hours_component = min(hours_logged / target_hours, 1.0) * HOURS_WEIGHT if target_hours > 0 else 0.0
    avg_conf = average_confidence(confidences) or 0.0
    confidence_component = (avg_conf / MAX_CONFIDENCE) * CONFIDENCE_WEIGHT

    return round(hours_component + confidence_component, 1)