"""Background worker for processing pending and retry events."""

import asyncio
import logging
import signal
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.database import get_db_context
from app.services.forwarding_service import ForwardingService

logger = logging.getLogger(__name__)


class RetryWorker:
    """
    Background worker that processes pending and retry events.

    Can be run as a standalone process or integrated with the main app.
    """

    def __init__(
        self,
        batch_size: int = 100,
        poll_interval: int = 10,
        retry_interval: int = 60,
    ):
        """
        Initialize the retry worker.

        Args:
            batch_size: Number of events to process per batch
            poll_interval: Seconds between polling for new events
            retry_interval: Seconds between retry checks
        """
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.retry_interval = retry_interval
        self._running = False
        self._shutdown_event: Optional[asyncio.Event] = None

    async def start(self) -> None:
        """Start the worker."""
        self._running = True
        self._shutdown_event = asyncio.Event()

        logger.info("Starting retry worker...")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info(f"Retry interval: {self.retry_interval}s")

        # Set up signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown)

        # Run processing loops concurrently
        await asyncio.gather(
            self._process_pending_loop(),
            self._process_retry_loop(),
        )

    def _handle_shutdown(self) -> None:
        """Handle shutdown signal."""
        logger.info("Shutdown signal received, stopping worker...")
        self._running = False
        if self._shutdown_event:
            self._shutdown_event.set()

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info("Stopping retry worker...")
        self._running = False
        if self._shutdown_event:
            self._shutdown_event.set()

    async def _process_pending_loop(self) -> None:
        """Loop to process pending events."""
        while self._running:
            try:
                stats = await self._process_pending_batch()
                if stats["processed"] > 0:
                    logger.info(
                        f"Processed {stats['processed']} pending events: "
                        f"{stats['succeeded']} succeeded, {stats['failed']} failed"
                    )
            except Exception as e:
                logger.exception("Error in pending events loop")

            # Wait for next poll
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.poll_interval,
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                pass  # Continue polling

    async def _process_retry_loop(self) -> None:
        """Loop to process retry events."""
        while self._running:
            try:
                stats = await self._process_retry_batch()
                if stats["processed"] > 0:
                    logger.info(
                        f"Processed {stats['processed']} retry events: "
                        f"{stats['succeeded']} succeeded, {stats['failed']} failed"
                    )
            except Exception as e:
                logger.exception("Error in retry events loop")

            # Wait for next retry check
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.retry_interval,
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                pass  # Continue checking

    async def _process_pending_batch(self) -> dict:
        """Process a batch of pending events."""
        async with get_db_context() as session:
            service = ForwardingService(session)
            return await service.process_batch(limit=self.batch_size)

    async def _process_retry_batch(self) -> dict:
        """Process a batch of retry events."""
        async with get_db_context() as session:
            service = ForwardingService(session)
            return await service.process_retries(limit=self.batch_size)


async def run_worker() -> None:
    """Run the retry worker as a standalone process."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    worker = RetryWorker(
        batch_size=settings.event_batch_size,
        poll_interval=10,
        retry_interval=60,
    )

    await worker.start()


def main() -> None:
    """Entry point for the worker."""
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
