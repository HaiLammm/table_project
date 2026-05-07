from datetime import UTC, datetime

from src.app.modules.dashboard.domain.entities import DiagnosticInsight
from src.app.modules.dashboard.domain.value_objects import PatternType


def test_diagnostic_insight_preserves_fields() -> None:
    created_at = datetime(2026, 5, 7, 8, 0, tzinfo=UTC)
    insight = DiagnosticInsight(
        id=12,
        user_id=7,
        type=PatternType.TIME_OF_DAY_PATTERN,
        severity="success",
        icon="clock",
        title="Morning sessions are a strength",
        text="Your accuracy looks strongest in the morning.",
        confidence_score=0.5,
        created_at=created_at,
    )

    assert insight.id == 12
    assert insight.user_id == 7
    assert insight.type is PatternType.TIME_OF_DAY_PATTERN
    assert insight.severity == "success"
    assert insight.created_at == created_at


def test_delivery_interval_tracks_confidence_stage() -> None:
    micro = DiagnosticInsight(
        user_id=1,
        type=PatternType.TIME_OF_DAY_PATTERN,
        severity="info",
        icon="clock",
        title="Quick insight",
        text="Morning is strong.",
        confidence_score=0.5,
    )
    medium = DiagnosticInsight(
        user_id=1,
        type=PatternType.CATEGORY_SPECIFIC_WEAKNESS,
        severity="warning",
        icon="alert-triangle",
        title="Category needs work",
        text="Nouns are weaker.",
        confidence_score=0.8,
    )
    full = DiagnosticInsight(
        user_id=1,
        type=PatternType.RESPONSE_TIME_ANOMALY,
        severity="warning",
        icon="trending-up",
        title="Slow cards slip",
        text="Slow cards are forgotten more often.",
        confidence_score=1.0,
    )

    assert micro.delivery_interval == 10
    assert medium.delivery_interval == 7
    assert full.delivery_interval == 5
