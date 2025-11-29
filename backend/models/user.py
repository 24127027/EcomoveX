from enum import Enum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base


class Role(str, Enum):
    user = "User"
    admin = "Admin"


class Activity(str, Enum):
    save_destination = "save destination"
    search_destination = "search destination"
    review_destination = "review destination"


class Rank(str, Enum):
    bronze = "Bronze"
    silver = "Silver"
    gold = "Gold"
    platinum = "Platinum"
    diamond = "Diamond"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_user_email_role", "email", "role"),
        Index("ix_user_rank_eco", "rank", "eco_point"),
        Index("ix_user_created", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    avt_blob_name = Column(String(255), nullable=True)
    cover_blob_name = Column(String(255), nullable=True)

    eco_point = Column(Integer, nullable=True, default=0)
    rank = Column(SQLEnum(Rank), nullable=True, default=Rank.bronze)
    role = Column(SQLEnum(Role), nullable=False, default=Role.user)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_bot = Column(Boolean, default=False)

    sent_messages = relationship(
        "Message",
        foreign_keys="[Message.sender_id]",
        back_populates="sender",
        cascade="all, delete-orphan",
    )
    rooms = relationship(
        "RoomMember", back_populates="user", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "Review", back_populates="user", cascade="all, delete-orphan"
    )
    missions = relationship(
        "UserMission", back_populates="user", cascade="all, delete-orphan"
    )
    clusters = relationship(
        "UserClusterAssociation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    saved_destinations = relationship(
        "UserSavedDestination",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activity_logs = relationship(
        "UserActivity", back_populates="user", cascade="all, delete-orphan"
    )
    files = relationship(
        "Metadata", back_populates="user", cascade="all, delete-orphan"
    )
    plan_members = relationship(
        "PlanMember", back_populates="user", cascade="all, delete-orphan"
    )
    friendships1 = relationship(
        "Friend",
        foreign_keys="[Friend.user1_id]",
        back_populates="user1",
        cascade="all, delete-orphan",
    )
    friendships2 = relationship(
        "Friend",
        foreign_keys="[Friend.user2_id]",
        back_populates="user2",
        cascade="all, delete-orphan",
    )
    friend_actions = relationship(
        "Friend",
        foreign_keys="[Friend.action_by]",
        back_populates="action_user",
        cascade="all, delete-orphan",
    )
    preference = relationship(
        "Preference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserActivity(Base):
    __tablename__ = "user_activities"
    __table_args__ = (
        Index("ix_user_activity_user_timestamp", "user_id", "timestamp"),
        Index("ix_user_activity_destination", "destination_id", "activity"),
        Index("ix_user_activity_type_timestamp", "activity", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    destination_id = Column(
        String(255),
        ForeignKey("destinations.place_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity = Column(SQLEnum(Activity), nullable=False)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="activity_logs")
    destination = relationship("Destination", back_populates="user_activities")
