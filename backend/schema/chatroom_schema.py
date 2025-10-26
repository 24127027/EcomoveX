from pydantic import BaseModel
from typing import List, Tuple
from datetime import datetime

class ChatRoomResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    username_joined_at: List[Tuple[str, datetime]]

    class Config:
        orm_mode = True