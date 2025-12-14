from pydantic import BaseModel

class ChatMessage(BaseModel):
    user_id: int
    room_id: int
    message: str
