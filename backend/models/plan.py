from enum import Enum
from sqlalchemy import Column, Date, Enum as SQLEnum, Float, ForeignKey, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import relationship
from database.db import Base

class DestinationType(str, Enum):
    restaurant = "restaurant"
    hotel = "hotel"
    attraction = "attraction"
    
class PlanRole(str, Enum):
    owner = "owner"
    member = "member"

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    place_name = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget_limit = Column(Float, nullable=True)

    destinations = relationship("PlanDestination", back_populates="plan", cascade="all, delete-orphan")
    members = relationship("PlanMember", back_populates="plan", cascade="all, delete-orphan")
    
class PlanMember(Base):
    __tablename__ = "plan_members"  
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'plan_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    role = Column(SQLEnum(PlanRole), default=PlanRole.member, nullable=False)

    user = relationship("User", back_populates="plan_members")
    plan = relationship("Plan", back_populates="members")

class PlanDestination(Base):
    __tablename__ = "plan_destinations"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(String(255), ForeignKey("destinations.google_place_id", ondelete="CASCADE"), nullable=False)
    type = Column(SQLEnum(DestinationType), nullable=False)
    visit_date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)

    plan = relationship("Plan", back_populates="destinations")
    destination = relationship("Destination", back_populates="plan_destinations")