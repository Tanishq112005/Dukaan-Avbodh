import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlmodel import select

from config.database import db_connection
from config.redis import redisClient
from models.product import Product
from models.probabilityValues import (
    ProbabilityOfShowingItems,
    ProbabilityOfShowingItemsForParticularUser,
)
from models.userEvent import UserEvent, EventType
from .base import BaseWorker

logger = logging.getLogger(__name__)

# Scoring weights based on user interaction events
EVENT_SCORE_WEIGHTS = {
    EventType.VIEWED.value: 1.0,           # Viewed -> +1
    EventType.ADD_TO_CART.value: 2.0,      # Add to cart -> +2
    EventType.PURCHASED.value: 5.0,        # Purchased -> +5
    EventType.REMOVE_FROM_CART.value: -2.0 # Remove from cart -> -2
}

REDIS_RAW_SCORES_KEY = "product:raw_scores"


class ProbabilityWorker(BaseWorker):
    """
    Worker that calculates scores for product events and updates
    ProbabilityOfShowingItems in the database.

    Also bulk-inserts consumed events into the UserEvent table in a single
    database operation (Write-Behind pattern), avoiding individual DB locks.

    Scoring rules:
      - viewed           -> +1 point
      - add_to_cart      -> +2 points
      - purchased        -> +5 points
      - remove_from_cart -> -2 points

    Normalization:
      Updated raw scores are divided by the total sum of all scores,
      ensuring probabilities are always bounded between 0.0 and 1.0,
      and their sum equals 1.0.
    """

    @classmethod
    def calculate_event_deltas(cls, events: List[dict]) -> tuple[Dict[int, float], Dict[tuple[int, int], float]]:
        """
        Aggregates points per product_id and (user_id, product_id).
        """
        global_deltas: Dict[int, float] = {}
        user_deltas: Dict[tuple[int, int], float] = {}

        for event in events:
            product_id = event.get("product_id")
            if product_id is None:
                continue

            event_type = str(event.get("event_type", "")).lower()
            points = EVENT_SCORE_WEIGHTS.get(event_type, 0.0)

            if points != 0.0:
                global_deltas[product_id] = global_deltas.get(product_id, 0.0) + points

                user_id = event.get("user_id")
                if user_id is not None:
                    key = (user_id, product_id)
                    user_deltas[key] = user_deltas.get(key, 0.0) + points

        return global_deltas, user_deltas

    @classmethod
    async def _async_process_events(cls, events: List[dict]) -> dict:
        global_deltas, user_deltas = cls.calculate_event_deltas(events)
        redis = redisClient.get_redis_client()

        async with db_connection.get_session() as session:
            # 1. Bulk persist consumed events to the UserEvent table (Write-Behind)
            if events:
                event_records = []
                for e in events:
                    try:
                        raw_ts = e.get("timestamp")
                        ts = datetime.fromisoformat(raw_ts) if raw_ts else datetime.now()
                        event_records.append(
                            UserEvent(
                                user_id=e["user_id"],
                                product_id=e.get("product_id"),
                                event_type=e["event_type"],
                                timestamp=ts
                            )
                        )
                    except Exception:
                        logger.warning("Skipping invalid event during bulk persist: %s", e)

                if event_records:
                    session.add_all(event_records)
                    logger.info("Bulk-persisted %d events into UserEvent table.", len(event_records))

            # 2. Fetch all product IDs from the database
            products = (await session.exec(select(Product.id))).all()
            all_product_ids = [p if isinstance(p, int) else p[0] for p in products]

            if not all_product_ids:
                logger.warning("No products found in database to calculate probabilities.")
                if events:
                    await session.commit()
                return {"success": False, "message": "No products in database."}

            # 3. Fetch or initialize cumulative raw scores from Redis
            raw_scores: Dict[int, float] = {}
            for pid in all_product_ids:
                cached_score = redis.hget(REDIS_RAW_SCORES_KEY, str(pid))
                if cached_score is not None:
                    try:
                        raw_scores[pid] = float(cached_score)
                    except (ValueError, TypeError):
                        raw_scores[pid] = 1.0
                else:
                    raw_scores[pid] = 1.0  # Base score for every product

            # 4. Apply event point deltas (+1, +2, +5, -2)
            for pid, delta in global_deltas.items():
                if pid in raw_scores:
                    raw_scores[pid] = max(0.0, raw_scores[pid] + delta)
                else:
                    raw_scores[pid] = max(0.0, 1.0 + delta)

            # Persist raw scores back to Redis
            if raw_scores:
                pipe = redis.pipeline()
                for pid, score in raw_scores.items():
                    pipe.hset(REDIS_RAW_SCORES_KEY, str(pid), score)
                pipe.execute()

            # 5. Normalization: divide each score by total sum (values always in [0, 1])
            total_sum = sum(raw_scores.values())
            probabilities: Dict[int, float] = {}

            if total_sum > 0.0:
                for pid, raw in raw_scores.items():
                    probabilities[pid] = raw / total_sum
            else:
                equal_prob = 1.0 / len(all_product_ids)
                for pid in all_product_ids:
                    probabilities[pid] = equal_prob

            # 6. Upsert into ProbabilityOfShowingItems table in Dukaan database
            existing_records = (
                await session.exec(select(ProbabilityOfShowingItems))
            ).all()
            existing_by_pid = {r.product_id: r for r in existing_records}

            for pid, prob in probabilities.items():
                prob_rounded = round(prob, 6)
                if pid in existing_by_pid:
                    existing_by_pid[pid].score = prob_rounded
                    session.add(existing_by_pid[pid])
                else:
                    new_record = ProbabilityOfShowingItems(
                        product_id=pid,
                        score=prob_rounded,
                    )
                    session.add(new_record)

            # 7. User-specific probability updates (if user events were present)
            if user_deltas:
                user_ids = {u for (u, _) in user_deltas.keys()}
                for uid in user_ids:
                    u_deltas = {p: d for (u, p), d in user_deltas.items() if u == uid}
                    u_raw: Dict[int, float] = {}
                    u_key = f"user_raw_scores:{uid}"

                    for pid in all_product_ids:
                        cached = redis.hget(u_key, str(pid))
                        base = float(cached) if cached else 1.0
                        if pid in u_deltas:
                            base = max(0.0, base + u_deltas[pid])
                        u_raw[pid] = base
                        redis.hset(u_key, str(pid), base)

                    u_sum = sum(u_raw.values())
                    for pid, val in u_raw.items():
                        u_prob = round((val / u_sum) if u_sum > 0 else (1.0 / len(all_product_ids)), 6)
                        u_existing = (await session.exec(
                            select(ProbabilityOfShowingItemsForParticularUser).where(
                                ProbabilityOfShowingItemsForParticularUser.user_id == uid,
                                ProbabilityOfShowingItemsForParticularUser.product_id == pid
                            )
                        )).first()
                        if u_existing:
                            u_existing.score = u_prob
                            session.add(u_existing)
                        else:
                            session.add(ProbabilityOfShowingItemsForParticularUser(
                                user_id=uid,
                                product_id=pid,
                                score=u_prob
                            ))

            # Commit all inserts and updates in one single transaction
            await session.commit()
            logger.info(
                "Successfully processed batch: %d events persisted, %d products updated.",
                len(events),
                len(probabilities)
            )

            return {
                "success": True,
                "events_persisted": len(events),
                "products_updated": len(probabilities),
                "total_sum": total_sum,
            }

    @classmethod
    def process_events(cls, events: List[dict]) -> dict:
        """
        Synchronous runner for the async event processing.
        """
        return asyncio.run(cls._async_process_events(events))

    @classmethod
    def run(cls, data: dict = None):
        """
        Worker method conforming to BaseWorker (can be called by RQ Worker or Consumer).
        Pops up to 100 events from the queue and processes them.
        """
        from task_queue.event_queue import event_queue

        batch_size = (data or {}).get("batch_size", 100)
        events = event_queue.pop_batch(max_items=batch_size)
        if not events:
            logger.info("[ProbabilityWorker] Queue is empty, nothing to process.")
            return {"events_processed": 0}

        logger.info("[ProbabilityWorker] Processing batch of %d events...", len(events))
        return cls.process_events(events)
