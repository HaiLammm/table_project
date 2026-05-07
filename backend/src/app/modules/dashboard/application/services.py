from collections import defaultdict
from datetime import UTC, datetime, timedelta
from statistics import mean
from uuid import UUID

import structlog

from src.app.modules.dashboard.domain.entities import DiagnosticInsight
from src.app.modules.dashboard.domain.interfaces import DiagnosticRepository, ReviewAnalyticsRow
from src.app.modules.dashboard.domain.value_objects import PatternType

logger = structlog.get_logger().bind(module="dashboard_service")


class DiagnosticsService:
    def __init__(self, diagnostic_repository: DiagnosticRepository) -> None:
        self._diagnostic_repository = diagnostic_repository

    async def compute_insights(self, user_id: int) -> list[DiagnosticInsight]:
        analytics = await self._diagnostic_repository.get_review_analytics(user_id, days_back=30)
        if not analytics:
            await self._diagnostic_repository.replace_insights(user_id, [])
            return []

        data_age_days = _data_age_days(analytics)
        if data_age_days < 3:
            await self._diagnostic_repository.replace_insights(user_id, [])
            logger.info(
                "diagnostics_skipped_insufficient_data",
                user_id=user_id,
                data_age_days=data_age_days,
            )
            return []

        confidence_score = _confidence_score(data_age_days)
        insights: list[DiagnosticInsight] = []

        time_of_day_insight = _detect_time_of_day_pattern(
            user_id=user_id,
            analytics=analytics,
            confidence_score=confidence_score,
        )
        if time_of_day_insight is not None:
            insights.append(time_of_day_insight)

        if confidence_score >= 0.8:
            category_insight = _detect_category_weakness(
                user_id=user_id,
                analytics=analytics,
                confidence_score=confidence_score,
            )
            if category_insight is not None:
                insights.append(category_insight)

            response_time_insight = _detect_response_time_anomaly(
                user_id=user_id,
                analytics=analytics,
                confidence_score=confidence_score,
            )
            if response_time_insight is not None:
                insights.append(response_time_insight)

        insights = insights[:3]
        expires_at = datetime.now(UTC) + timedelta(days=1)
        persisted_insights = [
            DiagnosticInsight(
                id=insight.id,
                user_id=insight.user_id,
                type=insight.type,
                severity=insight.severity,
                icon=insight.icon,
                title=insight.title,
                text=insight.text,
                action_label=insight.action_label,
                action_href=insight.action_href,
                confidence_score=insight.confidence_score,
                created_at=insight.created_at,
                expires_at=expires_at,
            )
            for insight in insights
        ]

        await self._diagnostic_repository.replace_insights(user_id, persisted_insights)
        logger.info(
            "diagnostic_insights_computed",
            user_id=user_id,
            count=len(persisted_insights),
        )
        return persisted_insights

    async def get_pending_insights(
        self,
        user_id: int,
        session_id: UUID,
        limit: int = 3,
    ) -> list[DiagnosticInsight]:
        if await self._diagnostic_repository.count_active_insights(user_id) == 0:
            await self.compute_insights(user_id)

        return await self._diagnostic_repository.get_pending_insights(user_id, session_id, limit)

    async def mark_insight_seen(self, insight_id: int, user_id: int, session_id: UUID) -> None:
        await self._diagnostic_repository.mark_insight_seen(insight_id, user_id, session_id)


def _data_age_days(analytics: list[ReviewAnalyticsRow]) -> int:
    first_review_at = min(row["reviewed_at"] for row in analytics)
    return (datetime.now(UTC).date() - first_review_at.date()).days + 1


def _confidence_score(data_age_days: int) -> float:
    if data_age_days >= 14:
        return 1.0
    if data_age_days >= 7:
        return 0.8
    return 0.5


def _period_for_hour(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 24:
        return "evening"
    return "late night"


def _accuracy(rows: list[ReviewAnalyticsRow]) -> float:
    if not rows:
        return 0.0
    passed = sum(1 for row in rows if row["rating"] >= 3)
    return passed / len(rows)


def _again_rate(rows: list[ReviewAnalyticsRow]) -> float:
    if not rows:
        return 0.0
    again = sum(1 for row in rows if row["rating"] == 1)
    return again / len(rows)


def _dashboard_link(confidence_score: float) -> tuple[str | None, str | None]:
    if confidence_score < 1.0:
        return None, None
    return "View analytics", "/dashboard"


def _detect_time_of_day_pattern(
    *,
    user_id: int,
    analytics: list[ReviewAnalyticsRow],
    confidence_score: float,
) -> DiagnosticInsight | None:
    grouped: dict[str, list[ReviewAnalyticsRow]] = defaultdict(list)
    for row in analytics:
        grouped[_period_for_hour(row["reviewed_at"].hour)].append(row)

    eligible = {period: rows for period, rows in grouped.items() if len(rows) >= 3}
    if len(eligible) < 2:
        return None

    accuracies = {period: _accuracy(rows) for period, rows in eligible.items()}
    best_period = max(accuracies, key=accuracies.get)
    worst_period = min(accuracies, key=accuracies.get)
    delta = accuracies[best_period] - accuracies[worst_period]
    if delta < 0.15:
        return None

    action_label, action_href = _dashboard_link(confidence_score)
    if confidence_score <= 0.5:
        title = "Quick insight"
        text = f"Your accuracy looks strongest in the {best_period}."
        action_label = None
        action_href = None
    else:
        gain = round(delta * 100)
        title = f"{best_period.title()} sessions are a strength"
        text = (
            f"Your recall is {gain}% stronger in {best_period} sessions than {worst_period} ones."
        )

    return DiagnosticInsight(
        user_id=user_id,
        type=PatternType.TIME_OF_DAY_PATTERN,
        severity="success",
        icon="clock",
        title=title,
        text=text,
        action_label=action_label,
        action_href=action_href,
        confidence_score=confidence_score,
    )


def _detect_category_weakness(
    *,
    user_id: int,
    analytics: list[ReviewAnalyticsRow],
    confidence_score: float,
) -> DiagnosticInsight | None:
    grouped: dict[str, list[ReviewAnalyticsRow]] = defaultdict(list)
    for row in analytics:
        category = row["term_category"]
        if category:
            grouped[category].append(row)

    eligible = {category: rows for category, rows in grouped.items() if len(rows) >= 3}
    if len(eligible) < 2:
        return None

    category_accuracies = {category: _accuracy(rows) for category, rows in eligible.items()}
    overall_average = mean(category_accuracies.values())
    weakest_category = min(category_accuracies, key=category_accuracies.get)
    weakest_accuracy = category_accuracies[weakest_category]
    gap = overall_average - weakest_accuracy
    if gap < 0.15:
        return None

    action_label, action_href = _dashboard_link(confidence_score)
    return DiagnosticInsight(
        user_id=user_id,
        type=PatternType.CATEGORY_SPECIFIC_WEAKNESS,
        severity="warning",
        icon="alert-triangle",
        title="One category needs reinforcement",
        text=(
            f"Your {weakest_category} cards are recalled {round(gap * 100)}% less often "
            "than your average."
        ),
        action_label=action_label,
        action_href=action_href,
        confidence_score=confidence_score,
    )


def _detect_response_time_anomaly(
    *,
    user_id: int,
    analytics: list[ReviewAnalyticsRow],
    confidence_score: float,
) -> DiagnosticInsight | None:
    rows_with_timing = [row for row in analytics if row["response_time_ms"] is not None]
    slow_rows = [row for row in rows_with_timing if (row["response_time_ms"] or 0) > 10_000]
    fast_rows = [row for row in rows_with_timing if (row["response_time_ms"] or 0) <= 10_000]
    if len(slow_rows) < 3 or len(fast_rows) < 3:
        return None

    slow_again_rate = _again_rate(slow_rows)
    fast_again_rate = _again_rate(fast_rows)
    delta = slow_again_rate - fast_again_rate
    if delta < 0.2:
        return None

    action_label, action_href = _dashboard_link(confidence_score)
    return DiagnosticInsight(
        user_id=user_id,
        type=PatternType.RESPONSE_TIME_ANOMALY,
        severity="warning",
        icon="trending-up",
        title="Slow cards tend to slip",
        text=(
            f"Cards taking over 10s are forgotten {round(delta * 100)}% more often. "
            "Consider breaking them into smaller chunks."
        ),
        action_label=action_label,
        action_href=action_href,
        confidence_score=confidence_score,
    )
