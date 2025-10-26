from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("ChatRoomMember", back_populates="chat_room")


class ChatRoomMember(Base):
    __tablename__ = "chat_room_members"

    chat_room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    joined_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint("chat_room_id", "user_id"),
    )

    chat_room = relationship("ChatRoom", back_populates="members")
    user = relationship("User", back_populates="chat_rooms")
