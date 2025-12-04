from enum import Enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from database.db import Base


class DestinationType(str, Enum):
    restaurant = "restaurant"
    accommodation = "accommodation"
    attraction = "attraction"
    transport = "transport"


class PlanRole(str, Enum):
    owner = "owner"
    member = "member"


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        Index("ix_plan_dates", "start_date", "end_date"),
        Index("ix_plan_created", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    place_name = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget_limit = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    destinations = relationship(
        "PlanDestination", back_populates="plan", cascade="all, delete-orphan"
    )
    members = relationship("PlanMember", back_populates="plan", cascade="all, delete-orphan")


class PlanDestination(Base):
    __tablename__ = "plan_destinations"
    __table_args__ = (
        Index("ix_plan_dest_date", "plan_id", "visit_date"),
        Index("ix_plan_dest_type", "plan_id", "type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_in_day = Column(Integer, nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(
        String(255),
        ForeignKey("destinations.place_id", ondelete="CASCADE"),
        nullable=False,
    )
    type = Column(SQLEnum(DestinationType), nullable=False, index=True)
    estimated_cost = Column(Float, nullable=True)
    visit_date = Column(DateTime, nullable=False)
    time = Column(Time, nullable=True)  # ✅ Thêm trường lưu thời gian buổi
    url = Column(String(512), nullable=True)
    note = Column(Text, nullable=True)

    plan = relationship("Plan", back_populates="destinations")
    destination = relationship("Destination", back_populates="plan_destinations")


class PlanMember(Base):
    __tablename__ = "plan_members"
    __table_args__ = (Index("ix_plan_member_role", "plan_id", "role"),)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    plan_id = Column(
        Integer,
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    role = Column(SQLEnum(PlanRole), default=PlanRole.member, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="plan_members")
    plan = relationship("Plan", back_populates="members")
