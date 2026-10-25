import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from UserEvents.models import UserEvent, EventType
from UserEvents.database import userEvent
from task_queue.event_queue import event_queue

logger = logging.getLogger(__name__)

_redis_available: bool = True


def _safe_queue_push(event_data: dict) -> None:
    """
    Attempts to push event to Redis queue. If Redis is unreachable,
    disables subsequent pushes for this session to avoid repeated connection timeouts.
    """
    global _redis_available
    if not _redis_available:
        return

    try:
        event_queue.push(event_data)
    except Exception as q_err:
        _redis_available = False
        logger.info(
            "Redis event queue is offline/unreachable (%s). Event logging will proceed directly via PostgreSQL.",
            q_err,
        )


async def record_user_event(
    user_id: Optional[int],
    product_id: Optional[int],
    event_type: EventType,
    category: Optional[str] = "general",
) -> bool:
    """
    Records a single user interaction event (e.g. ADD_TO_CART, REMOVE_FROM_CART, VIEWED).
    
    Rules & Invariants:
    - If user_id is None or <= 0 (guest browsing), the event is NOT stored.
    - If product_id is None, the event is NOT stored.
    - Pushes to Redis event_queue for real-time background processing (if Redis is online).
    - Persists directly into PostgreSQL via UserEvent repository so events are reliably
      saved across all runtime environments.
    - Never raises an unhandled exception to prevent tool or agent workflow crashes.
    """
    if user_id is None or user_id <= 0 or product_id is None:
        return False

    clean_category = (category or "general").strip()
    event_type_str = event_type.value if hasattr(event_type, "value") else str(event_type)
    now = datetime.now()

    # 1. Non-blocking queue push for background workers (if Redis is alive)
    _safe_queue_push({
        "user_id": user_id,
        "product_id": product_id,
        "event_type": event_type_str,
        "category": clean_category,
        "timestamp": now.isoformat(),
    })

    # 2. Persist directly to PostgreSQL database
    try:
        await userEvent.addUserEvents(
            user_id=user_id,
            event_type=event_type,
            product_id=product_id,
            category=clean_category,
        )
        return True
    except Exception as db_err:
        logger.warning(
            "Failed to save user event (user_id=%s, product_id=%s, type=%s): %s",
            user_id,
            product_id,
            event_type_str,
            db_err,
        )
        return False


async def record_bulk_user_events(
    user_id: Optional[int],
    product_ids: List[int],
    event_type: EventType,
    categories: Optional[Dict[int, str]] = None,
) -> int:
    """
    Records multiple user interaction events at once (e.g. batch VIEWED recommendations).
    
    Rules & Invariants:
    - If user_id is None or <= 0 (guest browsing), events are NOT stored.
    - If product_ids is empty, returns 0.
    - Pushes events to Redis event_queue if available.
    - Bulk-persists into PostgreSQL database in a single transaction.
    - Never raises an unhandled exception.
    """
    if user_id is None or user_id <= 0 or not product_ids:
        return 0

    now = datetime.now()
    event_type_str = event_type.value if hasattr(event_type, "value") else str(event_type)
    categories_map = categories or {}

    # 1. Push to Redis queue if online
    for pid in product_ids:
        cat = categories_map.get(pid, "general")
        _safe_queue_push({
            "user_id": user_id,
            "product_id": pid,
            "event_type": event_type_str,
            "category": cat,
            "timestamp": now.isoformat(),
        })

    # 2. Bulk insert to PostgreSQL database
    db_events = [
        UserEvent(
            user_id=user_id,
            product_id=pid,
            event_type=event_type,
            category=categories_map.get(pid, "general"),
            timestamp=now,
        )
        for pid in product_ids
    ]

    try:
        inserted = await userEvent.bulkAddUserEvents(db_events)
        return len(inserted)
    except Exception as db_err:
        logger.warning(
            "Failed to bulk-save user events (user_id=%s, count=%d, type=%s): %s",
            user_id,
            len(product_ids),
            event_type_str,
            db_err,
        )
        return 0
