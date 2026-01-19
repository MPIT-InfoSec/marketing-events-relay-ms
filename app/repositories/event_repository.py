"""Event repository."""

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import EventStatus
from app.models.event import MarketingEvent
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[MarketingEvent]):
    """Repository for MarketingEvent entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(MarketingEvent, session)

    async def get_by_event_id(self, event_id: str) -> Optional[MarketingEvent]:
        """Get event by external event_id."""
        result = await self.session.execute(
            select(MarketingEvent).where(MarketingEvent.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_with_attempts(self, id: int) -> Optional[MarketingEvent]:
        """Get event with attempts loaded."""
        result = await self.session.execute(
            select(MarketingEvent)
            .options(selectinload(MarketingEvent.attempts))
            .where(MarketingEvent.id == id)
        )
        return result.scalar_one_or_none()

    async def get_pending_events(
        self,
        limit: int = 100,
    ) -> Sequence[MarketingEvent]:
        """Get pending events for processing."""
        result = await self.session.execute(
            select(MarketingEvent)
            .options(selectinload(MarketingEvent.storefront))
            .where(MarketingEvent.status == EventStatus.PENDING)
            .order_by(MarketingEvent.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_events_for_retry(
        self,
        limit: int = 100,
    ) -> Sequence[MarketingEvent]:
        """Get events ready for retry."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(MarketingEvent)
            .options(selectinload(MarketingEvent.storefront))
            .where(
                MarketingEvent.status == EventStatus.RETRYING,
                MarketingEvent.next_retry_at <= now,
            )
            .order_by(MarketingEvent.next_retry_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_storefront(
        self,
        storefront_id: int,
        status: Optional[EventStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[MarketingEvent]:
        """Get events for a storefront with optional status filter."""
        query = select(MarketingEvent).where(
            MarketingEvent.storefront_id == storefront_id
        )

        if status:
            query = query.where(MarketingEvent.status == status)

        result = await self.session.execute(
            query.order_by(MarketingEvent.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update_status(
        self,
        id: int,
        status: EventStatus,
        error_message: Optional[str] = None,
        next_retry_at: Optional[datetime] = None,
        processed_at: Optional[datetime] = None,
        increment_retry: bool = False,
    ) -> None:
        """Update event status and related fields."""
        values = {"status": status}

        if error_message is not None:
            values["error_message"] = error_message
        if next_retry_at is not None:
            values["next_retry_at"] = next_retry_at
        if processed_at is not None:
            values["processed_at"] = processed_at

        stmt = update(MarketingEvent).where(MarketingEvent.id == id).values(**values)

        if increment_retry:
            stmt = stmt.values(retry_count=MarketingEvent.retry_count + 1)

        await self.session.execute(stmt)
        await self.session.flush()

    async def event_id_exists(self, event_id: str) -> bool:
        """Check if event_id already exists."""
        existing = await self.get_by_event_id(event_id)
        return existing is not None

    async def bulk_create(
        self,
        events: list[dict],
    ) -> Sequence[MarketingEvent]:
        """Bulk create events."""
        db_objs = [MarketingEvent(**event) for event in events]
        self.session.add_all(db_objs)
        await self.session.flush()
        for obj in db_objs:
            await self.session.refresh(obj)
        return db_objs
