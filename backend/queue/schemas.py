from pydantic import BaseModel, Field


class DataInputForSavingForMessage(BaseModel):
    last_seq : int 
