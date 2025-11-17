from enum import Enum
from sqlalchemy import Column, Date, Enum as SQLEnum, Float, ForeignKey, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import relationship
from database.user_database import UserBase

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
    user_plans = relationship("UserPlan", back_populates="plan", cascade="all, delete-orphan")
    
class UserPlan(UserBase):
    __tablename__ = "user_plans"
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'plan_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, primary_key=True)

    user = relationship("User", back_populates="user_plans")
    plan = relationship("Plan", back_populates="user_plans")

class PlanDestination(UserBase):
    __tablename__ = "plan_destinations"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(String(255), nullable=False)
    type = Column(SQLEnum(DestinationType), nullable=False)
    visit_date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)

    plan = relationship("Plan", back_populates="destinations")