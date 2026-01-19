"""Forwarding service for event delivery to platforms."""

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import KillSwitchError
from app.core.security import get_encryption
from app.models.enums import AttemptStatus, DestinationType, EventStatus
from app.models.event import MarketingEvent
from app.repositories.credential_repository import CredentialRepository
from app.repositories.event_attempt_repository import EventAttemptRepository
from app.repositories.event_repository import EventRepository
from app.repositories.sgtm_config_repository import SgtmConfigRepository

logger = logging.getLogger(__name__)


class ForwardingService:
    """Service for forwarding events to platforms via sGTM or direct APIs."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.event_repo = EventRepository(session)
        self.credential_repo = CredentialRepository(session)
        self.sgtm_repo = SgtmConfigRepository(session)
        self.attempt_repo = EventAttemptRepository(session)
        self.encryption = get_encryption()

    async def process_event(self, event: MarketingEvent) -> bool:
        """
        Process a single event, forwarding to all active credentials.

        Returns:
            True if at least one delivery succeeded, False otherwise
        """
        # Update status to processing
        await self.event_repo.update_status(event.id, EventStatus.PROCESSING)

        # Get active credentials for this storefront
        credentials = await self.credential_repo.get_active_credentials_for_event(
            event.storefront_id
        )

        if not credentials:
            logger.warning(f"No active credentials for storefront {event.storefront_id}")
            await self.event_repo.update_status(
                event.id,
                EventStatus.FAILED,
                error_message="No active credentials configured",
                processed_at=datetime.utcnow(),
            )
            return False

        # Parse event payload
        try:
            payload = json.loads(event.event_payload)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid event payload for event {event.id}: {e}")
            await self.event_repo.update_status(
                event.id,
                EventStatus.FAILED,
                error_message=f"Invalid JSON payload: {str(e)}",
                processed_at=datetime.utcnow(),
            )
            return False

        # Track delivery results
        any_success = False
        all_failed = True
        last_error = None

        for credential in credentials:
            # Skip if platform is disabled
            if not credential.platform.is_active:
                continue

            # Skip if storefront is disabled (double check)
            if not credential.storefront.is_active:
                continue

            try:
                success, error = await self._deliver_to_credential(
                    event, credential, payload
                )

                if success:
                    any_success = True
                    all_failed = False
                else:
                    last_error = error

            except Exception as e:
                logger.exception(
                    f"Error delivering event {event.id} to credential {credential.id}"
                )
                last_error = str(e)

                # Record failed attempt
                await self.attempt_repo.create_attempt(
                    event_id=event.id,
                    credential_id=credential.id,
                    destination_type=credential.destination_type,
                    status=AttemptStatus.FAILED,
                    error_message=str(e),
                )

        # Update final event status
        if any_success:
            await self.event_repo.update_status(
                event.id,
                EventStatus.DELIVERED,
                processed_at=datetime.utcnow(),
            )
        elif all_failed:
            # Schedule retry if possible
            from app.services.event_service import EventService
            event_service = EventService(self.session)
            await event_service.mark_failed(
                event.id,
                error_message=last_error or "All delivery attempts failed",
                can_retry=True,
            )

        return any_success

    async def _deliver_to_credential(
        self,
        event: MarketingEvent,
        credential,
        payload: dict,
    ) -> tuple[bool, Optional[str]]:
        """
        Deliver event to a specific credential.

        Returns:
            Tuple of (success, error_message)
        """
        import time

        start_time = time.time()

        try:
            # Decrypt credentials
            creds = self.encryption.decrypt(credential.credentials_encrypted)

            # Get sGTM config if using sGTM destination
            sgtm_config = None
            if credential.destination_type == DestinationType.SGTM:
                sgtm_config = await self.sgtm_repo.get_by_storefront_id(
                    credential.storefront_id
                )
                if not sgtm_config or not sgtm_config.is_active:
                    raise KillSwitchError("sGTM Config", credential.storefront_id)

            # Import adapter factory
            from app.adapters.factory import get_adapter

            # Get appropriate adapter
            adapter = get_adapter(credential.platform.platform_code)

            # Build delivery context
            context = {
                "event_type": event.event_type,
                "payload": payload,
                "credentials": creds,
                "pixel_id": credential.pixel_id,
                "account_id": credential.account_id,
                "sgtm_config": sgtm_config,
                "destination_type": credential.destination_type,
            }

            # Execute delivery
            result = await adapter.send(context)

            duration_ms = int((time.time() - start_time) * 1000)

            # Record attempt
            await self.attempt_repo.create_attempt(
                event_id=event.id,
                credential_id=credential.id,
                destination_type=credential.destination_type,
                status=AttemptStatus.SUCCESS if result.success else AttemptStatus.FAILED,
                http_status_code=result.status_code,
                response_body=result.response_body,
                error_message=result.error_message,
                duration_ms=duration_ms,
            )

            # Update credential usage
            await self.credential_repo.update_last_used(
                credential.id,
                error=result.error_message if not result.success else None,
            )

            return result.success, result.error_message

        except KillSwitchError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            await self.attempt_repo.create_attempt(
                event_id=event.id,
                credential_id=credential.id,
                destination_type=credential.destination_type,
                status=AttemptStatus.FAILED,
                error_message=error_msg,
                duration_ms=duration_ms,
            )

            return False, error_msg

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            await self.attempt_repo.create_attempt(
                event_id=event.id,
                credential_id=credential.id,
                destination_type=credential.destination_type,
                status=AttemptStatus.FAILED,
                error_message=error_msg,
                duration_ms=duration_ms,
            )

            return False, error_msg

    async def process_batch(self, limit: int = 100) -> dict:
        """
        Process a batch of pending events.

        Returns:
            Dict with processing statistics
        """
        events = await self.event_repo.get_pending_events(limit=limit)

        stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
        }

        for event in events:
            stats["processed"] += 1
            try:
                success = await self.process_event(event)
                if success:
                    stats["succeeded"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.exception(f"Error processing event {event.id}")
                stats["failed"] += 1

        return stats

    async def process_retries(self, limit: int = 100) -> dict:
        """
        Process events that are due for retry.

        Returns:
            Dict with retry statistics
        """
        events = await self.event_repo.get_events_for_retry(limit=limit)

        stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
        }

        for event in events:
            stats["processed"] += 1
            try:
                success = await self.process_event(event)
                if success:
                    stats["succeeded"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.exception(f"Error retrying event {event.id}")
                stats["failed"] += 1

        return stats
