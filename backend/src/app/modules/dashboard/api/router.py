from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.app.modules.auth.domain.exceptions import AuthenticationError
from src.app.modules.dashboard.api.dependencies import (
    CurrentUserDependency,
    get_diagnostics_service,
)
from src.app.modules.dashboard.api.schemas import (
    InsightResponse,
    MarkInsightSeenRequest,
    PendingInsightsResponse,
    SuccessResponse,
)
from src.app.modules.dashboard.application.services import DiagnosticsService

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

DiagnosticsServiceDependency = Annotated[DiagnosticsService, Depends(get_diagnostics_service)]


def _require_user_id(current_user: CurrentUserDependency) -> int:
    if current_user.id is None:
        msg = "Current user is missing an internal id"
        raise AuthenticationError(msg)
    return current_user.id


@router.get("/insights", response_model=PendingInsightsResponse)
async def read_pending_insights(
    current_user: CurrentUserDependency,
    diagnostics_service: DiagnosticsServiceDependency,
    session_id: Annotated[UUID, Query()],
    limit: Annotated[int, Query(ge=1, le=10)] = 3,
) -> PendingInsightsResponse:
    insights = await diagnostics_service.get_pending_insights(
        user_id=_require_user_id(current_user),
        session_id=session_id,
        limit=limit,
    )
    return PendingInsightsResponse(
        items=[InsightResponse.model_validate(insight) for insight in insights],
    )


@router.post("/insights/{insight_id}/seen", response_model=SuccessResponse)
async def mark_insight_seen(
    insight_id: int,
    payload: MarkInsightSeenRequest,
    current_user: CurrentUserDependency,
    diagnostics_service: DiagnosticsServiceDependency,
) -> SuccessResponse:
    await diagnostics_service.mark_insight_seen(
        insight_id=insight_id,
        user_id=_require_user_id(current_user),
        session_id=payload.session_id,
    )
    return SuccessResponse()
