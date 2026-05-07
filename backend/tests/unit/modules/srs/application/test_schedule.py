from datetime import UTC, datetime, timedelta
from math import ceil
from unittest.mock import AsyncMock

import pytest

from src.app.modules.srs.application.services import QueueStatsService
from src.app.modules.srs.domain.entities import (
    ScheduleBucket,
    UpcomingSchedule,
)


class MockScheduleRepository:
    def __init__(
        self, today: int, tomorrow: int, this_week: int, avg_ms: int | None = None
    ) -> None:
        self._today = today
        self._tomorrow = tomorrow
        self._this_week = this_week
        self._avg_ms = avg_ms if avg_ms is not None else 10000
        self._last_call_args: tuple | None = None

    async def count_due_cards_by_buckets(
        self, user_id: int, today_end: datetime, tomorrow_end: datetime, week_end: datetime
    ) -> UpcomingSchedule:
        self._last_call_args = (user_id, today_end, tomorrow_end, week_end)

        def calc_minutes(count: int) -> int:
            if count == 0:
                return 0
            return ceil(count * self._avg_ms / 60000)

        return UpcomingSchedule(
            today=ScheduleBucket(
                due_count=self._today, estimated_minutes=calc_minutes(self._today)
            ),
            tomorrow=ScheduleBucket(
                due_count=self._tomorrow, estimated_minutes=calc_minutes(self._tomorrow)
            ),
            this_week=ScheduleBucket(
                due_count=self._this_week, estimated_minutes=calc_minutes(self._this_week)
            ),
        )

    async def get_queue_stats(self, user_id: int, now: datetime):
        pass

    async def list_due_cards(self, user_id: int, now: datetime, mode, limit: int, offset: int):
        pass

    async def create_card(self, card):
        pass

    async def update_card(self, card):
        pass

    async def get_card_by_id(self, card_id: int, user_id: int):
        pass

    async def get_card_by_id_for_update(self, card_id: int, user_id: int):
        pass

    async def create_review(self, review):
        pass

    async def save_review_result(self, card, review):
        pass

    async def rollback(self):
        pass

    async def delete_review(self, review_id: int):
        pass

    async def get_last_review(self, card_id: int, user_id: int):
        pass

    async def get_last_review_for_update(self, card_id: int, user_id: int):
        pass

    async def update_card_with_delete_review(self, card, review_id: int):
        pass

    async def get_session_reviews(self, user_id: int, session_id):
        return []

    async def count_due_cards_for_date(self, user_id: int, date_end: datetime) -> int:
        return 0


@pytest.mark.asyncio
async def test_get_upcoming_schedule_returns_all_three_buckets() -> None:
    repo = MockScheduleRepository(today=5, tomorrow=3, this_week=12, avg_ms=8000)
    service = QueueStatsService(repo)

    schedule = await service.get_upcoming_schedule(user_id=1)

    assert schedule.today.due_count == 5
    assert schedule.tomorrow.due_count == 3
    assert schedule.this_week.due_count == 12


@pytest.mark.asyncio
async def test_no_double_counting_across_buckets() -> None:
    repo = MockScheduleRepository(today=10, tomorrow=8, this_week=20, avg_ms=5000)
    service = QueueStatsService(repo)

    schedule = await service.get_upcoming_schedule(user_id=1)

    assert (
        schedule.today.due_count + schedule.tomorrow.due_count + schedule.this_week.due_count == 38
    )
    assert schedule.today.due_count == 10
    assert schedule.tomorrow.due_count == 8
    assert schedule.this_week.due_count == 20


@pytest.mark.asyncio
async def test_empty_state_all_zeros() -> None:
    repo = MockScheduleRepository(today=0, tomorrow=0, this_week=0)
    service = QueueStatsService(repo)

    schedule = await service.get_upcoming_schedule(user_id=1)

    assert schedule.today.due_count == 0
    assert schedule.today.estimated_minutes == 0
    assert schedule.tomorrow.due_count == 0
    assert schedule.tomorrow.estimated_minutes == 0
    assert schedule.this_week.due_count == 0
    assert schedule.this_week.estimated_minutes == 0


@pytest.mark.asyncio
async def test_estimated_minutes_uses_avg_response_time() -> None:
    repo = MockScheduleRepository(today=6, tomorrow=0, this_week=0, avg_ms=15000)
    service = QueueStatsService(repo)

    schedule = await service.get_upcoming_schedule(user_id=1)

    assert schedule.today.due_count == 6
    assert schedule.today.estimated_minutes == ceil(6 * 15000 / 60000)


@pytest.mark.asyncio
async def test_estimated_minutes_falls_back_to_10s_per_card() -> None:
    repo = MockScheduleRepository(today=6, tomorrow=0, this_week=0, avg_ms=None)
    service = QueueStatsService(repo)

    schedule = await service.get_upcoming_schedule(user_id=1)

    assert schedule.today.due_count == 6
    assert schedule.today.estimated_minutes == ceil(6 * 10 / 60)


@pytest.mark.asyncio
async def test_bucket_boundaries_are_passed_to_repository() -> None:
    repo = MockScheduleRepository(today=0, tomorrow=0, this_week=0)
    service = QueueStatsService(repo)

    await service.get_upcoming_schedule(user_id=1)

    assert repo._last_call_args is not None
    user_id, today_end, tomorrow_end, week_end = repo._last_call_args
    assert user_id == 1
    assert today_end.hour == 23 and today_end.minute == 59 and today_end.second == 59
    assert tomorrow_end > today_end
    assert week_end > tomorrow_end


@pytest.mark.asyncio
async def test_sunday_edge_case_week_end_equals_today_end() -> None:
    now = datetime.now(UTC)
    if now.weekday() == 6:
        repo = MockScheduleRepository(today=5, tomorrow=0, this_week=0)
        service = QueueStatsService(repo)

        await service.get_upcoming_schedule(user_id=1)

        _, today_end, tomorrow_end, week_end = repo._last_call_args
        assert week_end == today_end


@pytest.mark.asyncio
async def test_correct_tomorrow_bucket_when_today_is_saturday() -> None:
    repo = MockScheduleRepository(today=5, tomorrow=3, this_week=10)
    service = QueueStatsService(repo)

    schedule = await service.get_upcoming_schedule(user_id=1)

    assert schedule.tomorrow.due_count == 3
    assert schedule.this_week.due_count == 10
