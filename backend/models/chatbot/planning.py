from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base
from models.chatbot.chat_session import ChatSession
# models/planning.py
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, ForeignKey, JSON, func, Text
)
from sqlalchemy.orm import relationship
from database.db import Base

class TravelPlan(Base):
    __tablename__ = "travel_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True)
    destination = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    meta = Column(JSON, nullable=True)  # budget, eco_mode, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship("PlanItem", back_populates="plan", cascade="all, delete-orphan")

class PlanItem(Base):
    __tablename__ = "plan_items"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("travel_plans.id", ondelete="CASCADE"), nullable=False)
    day_index = Column(Integer, nullable=False)         # day within trip: 1..N
    time = Column(String(32), nullable=True)            # e.g. "08:00"
    title = Column(String(255), nullable=False)
    type = Column(String(64), nullable=True)            # "activity","transport","food"
    meta = Column(JSON, nullable=True)                  # POI id, co2, notes...
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plan = relationship("TravelPlan", back_populates="items")

# stored session/context
class ChatSessionContext(Base):
    __tablename__ = "chat_session_context"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(128), nullable=False)
    value = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    session = relationship("ChatSession", back_populates="contexts")
