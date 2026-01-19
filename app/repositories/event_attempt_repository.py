"""Event Attempt repository."""

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import AttemptStatus
from app.models.event_attempt import EventAttempt
from app.repositories.base import BaseRepository


class EventAttemptRepository(BaseRepository[EventAttempt]):
    """Repository for EventAttempt entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(EventAttempt, session)

    async def get_by_event(
        self,
        event_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[EventAttempt]:
        """Get all attempts for an event."""
        result = await self.session.execute(
            select(EventAttempt)
            .options(selectinload(EventAttempt.credential))
            .where(EventAttempt.event_id == event_id)
            .order_by(EventAttempt.attempted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_credential(
        self,
        credential_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[EventAttempt]:
        """Get all attempts for a credential."""
        result = await self.session.execute(
            select(EventAttempt)
            .where(EventAttempt.credential_id == credential_id)
            .order_by(EventAttempt.attempted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent_attempts(
        self,
        hours: int = 24,
        status: Optional[AttemptStatus] = None,
        limit: int = 100,
    ) -> Sequence[EventAttempt]:
        """Get recent attempts within specified hours."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = select(EventAttempt).where(EventAttempt.attempted_at >= cutoff)

        if status:
            query = query.where(EventAttempt.status == status)

        result = await self.session.execute(
            query.order_by(EventAttempt.attempted_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def count_by_status(
        self,
        event_id: int,
    ) -> dict[str, int]:
        """Count attempts by status for an event."""
        result = await self.session.execute(
            select(EventAttempt.status, func.count(EventAttempt.id))
            .where(EventAttempt.event_id == event_id)
            .group_by(EventAttempt.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def get_success_rate(
        self,
        credential_id: int,
        hours: int = 24,
    ) -> float:
        """Calculate success rate for a credential in recent hours."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        total_result = await self.session.execute(
            select(func.count(EventAttempt.id)).where(
                EventAttempt.credential_id == credential_id,
                EventAttempt.attempted_at >= cutoff,
            )
        )
        total = total_result.scalar_one()

        if total == 0:
            return 1.0

        success_result = await self.session.execute(
            select(func.count(EventAttempt.id)).where(
                EventAttempt.credential_id == credential_id,
                EventAttempt.attempted_at >= cutoff,
                EventAttempt.status == AttemptStatus.SUCCESS,
            )
        )
        success = success_result.scalar_one()

        return success / total

    async def create_attempt(
        self,
        event_id: int,
        credential_id: int,
        destination_type: str,
        status: AttemptStatus,
        http_status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> EventAttempt:
        """Create a new attempt record."""
        return await self.create(
            {
                "event_id": event_id,
                "credential_id": credential_id,
                "destination_type": destination_type,
                "status": status,
                "http_status_code": http_status_code,
                "response_body": response_body[:5000] if response_body else None,
                "error_message": error_message,
                "duration_ms": duration_ms,
            }
        )
