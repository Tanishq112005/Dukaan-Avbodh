import logging
from datetime import datetime
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from UserEvents.database import userEvent
from UserEvents.schemas import UserEvent
from task_queue.event_queue import event_queue

logger = logging.getLogger(__name__)


class UserEventController:

    async def addUserEvent(
        self,
        payload: UserEvent,
        user_id: int
    ):
        """
        Queue-First (Write-Behind) pattern:
        Pushes event to Redis in-memory queue (~1-2ms) without locking or waiting
        on a synchronous database commit. The background worker bulk-inserts the events
        into PostgreSQL and updates ProbabilityOfShowingItems.
        """
        try:
            event_type_str = (
                payload.event_type.value
                if hasattr(payload.event_type, "value")
                else str(payload.event_type)
            )

            # Fast in-memory push to Redis queue
            event_queue.push({
                "user_id": user_id,
                "product_id": payload.product_id,
                "event_type": event_type_str,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "success": True,
                "msg": "Event queued successfully"
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        except Exception:
            logger.exception("Failed to queue user event")
            raise HTTPException(
                status_code=500,
                detail="Failed to queue user event"
            )

    async def getUserEvents(self, user_id: int):
        try:
            result = await userEvent.getEventsOfUser(user_id=user_id)

            return {
                "success": True,
                "msg": jsonable_encoder(result)
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Failed to get user events"
            )

    async def getAllUserEvent(self, limit: int):
        try:
            result = await userEvent.getRecentEventsOfUser(limit=limit)

            return {
                "success": True,
                "msg": jsonable_encoder(result)
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Failed to get events"
            )


userEventController = UserEventController()
