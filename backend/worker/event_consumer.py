import time
import logging
import asyncio
from typing import List, Optional, Dict, Any

from task_queue.event_queue import event_queue, EventQueue
from .probability_worker import ProbabilityWorker

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 1800  # 30 minutes
DEFAULT_BATCH_SIZE = 100          # Maximum 100 events at a time


class EventConsumer:
    """
    Consumer that picks up to 100 events from the queue and triggers
    ProbabilityWorker to calculate points and normalize probabilities.
    Can be run as a one-shot batch, an RQ job, or a 30-minute interval loop.
    """

    def __init__(self, queue: Optional[EventQueue] = None):
        self.queue = queue or event_queue
        self.worker = ProbabilityWorker

    def consume_batch(self, max_items: int = DEFAULT_BATCH_SIZE) -> List[dict]:
        """Pops up to 100 events from the queue."""
        return self.queue.pop_batch(max_items=max_items)

    def consume_and_process(self, max_items: int = DEFAULT_BATCH_SIZE) -> dict:
        """
        Consumes up to `max_items` (maximum 100) from the queue and processes them.
        """
        events = self.consume_batch(max_items=max_items)
        if not events:
            logger.info("[EventConsumer] No events waiting in queue.")
            return {
                "events_processed": 0,
                "message": "Queue was empty."
            }

        logger.info("[EventConsumer] Consumed %d events. Delegating to ProbabilityWorker...", len(events))
        result = self.worker.process_events(events)
        return {
            "events_processed": len(events),
            "result": result
        }

    def start_periodic_loop(
        self,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        max_items: int = DEFAULT_BATCH_SIZE
    ):
        """
        Synchronous infinite loop running every 30 minutes (1800s).
        Consumes up to 100 events in each cycle.
        """
        logger.info(
            "[EventConsumer] Starting 30-min periodic loop (interval=%ds, max_items=%d)...",
            interval_seconds,
            max_items
        )
        while True:
            try:
                self.consume_and_process(max_items=max_items)
            except Exception:
                logger.exception("[EventConsumer] Error during periodic processing cycle")

            logger.info("[EventConsumer] Waiting %ds before next batch...", interval_seconds)
            time.sleep(interval_seconds)

    async def start_async_periodic_loop(
        self,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        max_items: int = DEFAULT_BATCH_SIZE
    ):
        """
        Async infinite loop running every 30 minutes (for FastAPI background task).
        """
        logger.info(
            "[EventConsumer] Starting async 30-min periodic loop (interval=%ds)...",
            interval_seconds
        )
        while True:
            try:
                self.consume_and_process(max_items=max_items)
            except Exception:
                logger.exception("[EventConsumer] Error during async periodic processing cycle")

            await asyncio.sleep(interval_seconds)


# Shared instance
event_consumer = EventConsumer()
