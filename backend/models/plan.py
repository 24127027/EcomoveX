from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.user_database import UserBase
from enum import Enum

class DestinationType(str, Enum):
    restaurant = "restaurant"
    hotel = "hotel"
    attraction = "attraction"

class Plan(UserBase):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    place_name = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget_limit = Column(Float, nullable=True)

    destinations = relationship("PlanDestination", back_populates="plan", cascade="all, delete-orphan")
    user = relationship("User", back_populates="plans")

class PlanDestination(UserBase):
    __tablename__ = "plan_destinations"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(Integer, nullable=False)  # No FK - destination in separate DB
    type = Column(SQLEnum(DestinationType), nullable=False)
    visit_date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)

    plan = relationship("Plan", back_populates="destinations")