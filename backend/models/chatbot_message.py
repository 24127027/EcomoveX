from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database.db import Base


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    room_id = Column(Integer, index=True)

    sender = Column(String, nullable=False) 
    message = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
