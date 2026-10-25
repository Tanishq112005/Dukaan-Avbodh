from pydantic import BaseModel
from UserEvents.models import EventType


class UserEvent(BaseModel):
    product_id: int
    event_type: EventType
