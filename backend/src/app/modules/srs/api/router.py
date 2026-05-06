from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.app.modules.auth.domain.exceptions import AuthenticationError
from src.app.modules.srs.api.dependencies import (
    CurrentUserDependency,
    get_queue_stats_service,
)
from src.app.modules.srs.api.schemas import DueCardResponse, DueCardsResponse, QueueStatsResponse
from src.app.modules.srs.application.services import QueueStatsService
from src.app.modules.srs.domain.value_objects import QueueMode

router = APIRouter()

QueueStatsServiceDependency = Annotated[QueueStatsService, Depends(get_queue_stats_service)]
type QueueModeQuery = Annotated[QueueMode, Query()]
type QueueLimitQuery = Annotated[int, Query(ge=1, le=100)]
type QueueOffsetQuery = Annotated[int, Query(ge=0)]


def _require_user_id(current_user: CurrentUserDependency) -> int:
    if current_user.id is None:
        msg = "Current user is missing an internal id"
        raise AuthenticationError(msg)

    return current_user.id


@router.get("/queue-stats", response_model=QueueStatsResponse, tags=["srs_cards"])
async def read_queue_stats(
    current_user: CurrentUserDependency,
    queue_stats_service: QueueStatsServiceDependency,
) -> QueueStatsResponse:
    queue_stats = await queue_stats_service.get_queue_stats(_require_user_id(current_user))
    return QueueStatsResponse.model_validate(queue_stats)


@router.get("/queue", response_model=DueCardsResponse, tags=["srs_cards"])
async def read_due_queue(
    current_user: CurrentUserDependency,
    queue_stats_service: QueueStatsServiceDependency,
    mode: QueueModeQuery = QueueMode.FULL,
    limit: QueueLimitQuery = 100,
    offset: QueueOffsetQuery = 0,
) -> DueCardsResponse:
    due_cards = await queue_stats_service.get_due_cards(
        user_id=_require_user_id(current_user),
        mode=mode,
        limit=limit,
        offset=offset,
    )
    return DueCardsResponse(
        items=[
            DueCardResponse.model_validate(card) for card in due_cards.items if card.id is not None
        ],
        total_count=due_cards.total_count,
        limit=due_cards.limit,
        offset=due_cards.offset,
        mode=due_cards.mode,
    )
