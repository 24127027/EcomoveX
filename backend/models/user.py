from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    eco_point = Column(Integer, default=0)
    rank = Column(String(50), default="Newbie")

    # relationships
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    sent_messages = relationship("Chat", foreign_keys="[Chat.sender_id]", back_populates="sender")
    received_messages = relationship("Chat", foreign_keys="[Chat.receiver_id]", back_populates="receiver")
    rewards = relationship("UserReward", back_populates="user")
    chat_rooms = relationship("ChatRoomMember", back_populates="user")