from pydantic import BaseModel
from models.userEvent import EventType

class UserEvent(BaseModel):
    product_id : int
    event_type: EventType 
 
    