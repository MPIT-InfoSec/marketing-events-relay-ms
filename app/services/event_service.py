"""Event service for business logic."""

import json
from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, KillSwitchError, NotFoundError, ValidationError
from app.models.enums import EventStatus
from app.models.event import MarketingEvent
from app.repositories.event_repository import EventRepository
from app.repositories.storefront_repository import StorefrontRepository
from app.schemas.event import EventBatchRequest


class EventService:
    """Service for event operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = EventRepository(session)
        self.storefront_repo = StorefrontRepository(session)
        self._storefront_cache: dict[str, tuple[int, bool]] = {}  # Cache: storefront_id -> (id, is_active)

    async def get_by_id(self, id: int, with_attempts: bool = False) -> MarketingEvent:
        """Get event by ID."""
        if with_attempts:
            event = await self.repository.get_with_attempts(id)
        else:
            event = await self.repository.get_by_id(id)

        if not event:
            raise NotFoundError("Event", id)
        return event

    async def get_by_event_id(self, event_id: str) -> MarketingEvent:
        """Get event by external event_id."""
        event = await self.repository.get_by_event_id(event_id)
        if not event:
            raise NotFoundError("Event", event_id)
        return event

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        storefront_id: Optional[int] = None,
        status: Optional[EventStatus] = None,
    ) -> tuple[Sequence[MarketingEvent], int]:
        """Get all events with pagination and filters."""
        filters = {}
        if storefront_id is not None:
            filters["storefront_id"] = storefront_id
        if status is not None:
            filters["status"] = status

        events = await self.repository.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.repository.count(filters=filters)
        return events, total

    async def _get_storefront_info(self, storefront_id: str) -> tuple[int, bool]:
        """Get storefront ID and active status, using cache."""
        if storefront_id not in self._storefront_cache:
            storefront = await self.storefront_repo.get_by_storefront_id(storefront_id)
            if storefront:
                self._storefront_cache[storefront_id] = (storefront.id, storefront.is_active)
            else:
                self._storefront_cache[storefront_id] = (0, False)  # Not found marker
        return self._storefront_cache[storefront_id]

    async def ingest_batch(
        self,
        batch: EventBatchRequest,
    ) -> tuple[list[str], list[dict[str, str]]]:
        """
        Ingest a batch of events from OMS.

        Events are grouped by storefront_id from the data array.
        Each event's order_id serves as the unique event identifier.

        Returns:
            Tuple of (accepted_event_ids, errors)
        """
        # Check for error in batch
        if batch.error:
            raise ValidationError(
                f"Batch contains error: {batch.error}",
                details={"batch_error": batch.error},
            )

        accepted_ids = []
        errors = []
        events_to_create = []

        # Clear storefront cache for fresh lookup
        self._storefront_cache.clear()

        for event_item in batch.data:
            # Use order_id as unique event identifier
            event_id = event_item.order_id

            # Get storefront info (cached)
            sf_id, sf_active = await self._get_storefront_info(event_item.storefront_id)

            # Check if storefront exists
            if sf_id == 0:
                errors.append({
                    "event_id": event_id,
                    "error": f"Storefront '{event_item.storefront_id}' not found",
                })
                continue

            # Check kill switch
            if not sf_active:
                errors.append({
                    "event_id": event_id,
                    "error": f"Storefront '{event_item.storefront_id}' is disabled",
                })
                continue

            # Check for duplicate event_id
            if await self.repository.event_id_exists(event_id):
                errors.append({
                    "event_id": event_id,
                    "error": "Event already exists",
                })
                continue

            # Build event payload from the event item
            event_payload = event_item.to_event_payload()

            events_to_create.append({
                "event_id": event_id,
                "storefront_id": sf_id,
                "event_type": event_item.event_name.lower(),
                "event_payload": json.dumps(event_payload),
                "source_system": "oms",
                "status": EventStatus.PENDING,
            })
            accepted_ids.append(event_id)

        # Bulk create events
        if events_to_create:
            await self.repository.bulk_create(events_to_create)

        return accepted_ids, errors

    async def get_pending_events(self, limit: int = 100) -> Sequence[MarketingEvent]:
        """Get pending events for processing."""
        return await self.repository.get_pending_events(limit=limit)

    async def get_events_for_retry(self, limit: int = 100) -> Sequence[MarketingEvent]:
        """Get events ready for retry."""
        return await self.repository.get_events_for_retry(limit=limit)

    async def mark_processing(self, id: int) -> None:
        """Mark event as processing."""
        await self.repository.update_status(id, EventStatus.PROCESSING)

    async def mark_delivered(self, id: int) -> None:
        """Mark event as delivered."""
        await self.repository.update_status(
            id,
            EventStatus.DELIVERED,
            processed_at=datetime.utcnow(),
        )

    async def mark_failed(
        self,
        id: int,
        error_message: str,
        can_retry: bool = True,
    ) -> None:
        """Mark event as failed, optionally scheduling retry."""
        event = await self.get_by_id(id)

        if can_retry and event.retry_count < settings.max_retry_attempts:
            # Calculate exponential backoff
            backoff = settings.retry_backoff_base * (2 ** event.retry_count)
            next_retry = datetime.utcnow() + timedelta(seconds=backoff)

            await self.repository.update_status(
                id,
                EventStatus.RETRYING,
                error_message=error_message,
                next_retry_at=next_retry,
                increment_retry=True,
            )
        else:
            await self.repository.update_status(
                id,
                EventStatus.FAILED,
                error_message=error_message,
                processed_at=datetime.utcnow(),
            )

    async def get_by_storefront(
        self,
        storefront_id: int,
        status: Optional[EventStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[MarketingEvent]:
        """Get events for a storefront."""
        return await self.repository.get_by_storefront(
            storefront_id,
            status=status,
            skip=skip,
            limit=limit,
        )
