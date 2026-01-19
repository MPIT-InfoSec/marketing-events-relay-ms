"""Event ingestion endpoints."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_event_service, require_auth
from app.schemas.event import EventBatchRequest, EventBatchResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "",
    response_model=EventBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest marketing events",
    description="Accept a batch of marketing events for processing",
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Storefront not found"},
        503: {"description": "Storefront disabled (kill switch)"},
    },
)
async def ingest_events(
    batch: EventBatchRequest,
    _: str = Depends(require_auth),
    service: EventService = Depends(get_event_service),
) -> EventBatchResponse:
    """
    Ingest a batch of marketing events.

    Events are validated and queued for asynchronous processing.
    Duplicate event_ids are rejected.
    """
    accepted_ids, errors = await service.ingest_batch(batch)

    return EventBatchResponse(
        accepted=len(accepted_ids),
        rejected=len(errors),
        event_ids=accepted_ids,
        errors=errors,
    )
