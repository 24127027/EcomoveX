from enum import Enum
import json
from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base


class GreenVerifiedStatus(str, Enum):
    Green_Certified = "Green Certified"
    Not_Green_Verified = "Not Green Verified"
    AI_Green_Verified = "AI Green Verified"


class Destination(Base):
    __tablename__ = "destinations"
    __table_args__ = (Index("ix_destination_green_verified", "green_verified"),)

    place_id = Column(String(255), primary_key=True, nullable=False)
    green_verified = Column(
        SQLEnum(GreenVerifiedStatus),
        default=GreenVerifiedStatus.Not_Green_Verified,
    )

    reviews = relationship(
        "Review", back_populates="destination", cascade="all, delete-orphan"
    )
    plan_destinations = relationship(
        "PlanDestination",
        back_populates="destination",
        cascade="all, delete-orphan",
    )
    user_saved_destinations = relationship(
        "UserSavedDestination",
        back_populates="destination",
        cascade="all, delete-orphan",
    )
    cluster_destinations = relationship(
        "ClusterDestination",
        back_populates="destination",
        cascade="all, delete-orphan",
    )
    user_activities = relationship(
        "UserActivity",
        back_populates="destination",
        cascade="all, delete-orphan",
    )
    embedding = relationship(
        "DestinationEmbedding",
        back_populates="destination",
        uselist=False,
    )


class DestinationEmbedding(Base):
    __tablename__ = "destination_embeddings"
    __table_args__ = (Index("ix_embedding_model_version", "model_version"),)

    destination_id = Column(
        String(255),
        ForeignKey("destinations.place_id", ondelete="CASCADE"),
        primary_key=True,
    )
    embedding_vector = Column(Text, nullable=False)
    model_version = Column(String(50), default="v1", nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    destination = relationship("Destination", back_populates="embedding", uselist=False)

    def set_vector(self, vector: list[float]):
        self.embedding_vector = json.dumps(vector)

    def get_vector(self) -> list[float]:
        return json.loads(self.embedding_vector)


class UserSavedDestination(Base):
    __tablename__ = "user_saved_destinations"
    __table_args__ = (
        Index("ix_user_saved_dest", "user_id", "destination_id"),
        Index("ix_saved_at", "saved_at"),
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    destination_id = Column(
        String(255),
        ForeignKey("destinations.place_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="saved_destinations")
    destination = relationship("Destination", back_populates="user_saved_destinations")
