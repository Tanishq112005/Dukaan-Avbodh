from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from repositories.userEvent import userEvent
from schemas.userEvent import UserEvent


class UserEventController:

    async def addUserEvent(
        self,
        payload: UserEvent,
        user_id: int
    ):
        try:
            await userEvent.addUserEvents(
                user_id=user_id,
                event_type=payload.event_type,
                product_id=payload.product_id
            )

            return {
                "success": True,
                "msg": "Event successfully inserted"
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Failed to insert user event"
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