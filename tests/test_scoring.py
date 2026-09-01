"""Unit tests for the pure readiness-scoring functions (no DB, no API)."""
from app import scoring


def test_no_sessions_means_zero_readiness():
    assert scoring.readiness_score(hours_logged=0, target_hours=20, confidences=[]) == 0.0


def test_full_hours_and_max_confidence_is_100():
    score = scoring.readiness_score(hours_logged=20, target_hours=20, confidences=[5, 5, 5])
    assert score == 100.0


def test_overshooting_target_hours_does_not_exceed_60_hour_component():
    score_at_target = scoring.readiness_score(hours_logged=20, target_hours=20, confidences=[3])
    score_double_target = scoring.readiness_score(hours_logged=40, target_hours=20, confidences=[3])
    assert score_at_target == score_double_target


def test_hours_progress_pct_caps_at_100():
    assert scoring.hours_progress_pct(hours_logged=50, target_hours=20) == 100.0
    assert scoring.hours_progress_pct(hours_logged=10, target_hours=20) == 50.0


def test_average_confidence_none_when_no_sessions():
    assert scoring.average_confidence([]) is None
