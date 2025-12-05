from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


class Cluster(Base):
    __tablename__ = "clusters"
    __table_args__ = (Index("ix_cluster_name_algorithm", "name", "algorithm"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    algorithm = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)  # Thêm mô tả
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    users = relationship(
        "UserClusterAssociation", back_populates="cluster", cascade="all, delete-orphan"
    )
    destinations = relationship(
        "ClusterDestination", back_populates="cluster", cascade="all, delete-orphan"
    )
    preferences = relationship("Preference", back_populates="cluster")


class UserClusterAssociation(Base):
    __tablename__ = "user_cluster_associations"
    __table_args__ = (Index("ix_user_cluster", "user_id", "cluster_id"),)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    cluster_id = Column(
        Integer,
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="clusters")
    cluster = relationship("Cluster", back_populates="users")


class ClusterDestination(Base):
    __tablename__ = "cluster_destinations"
    __table_args__ = (Index("ix_cluster_dest_score", "cluster_id", "popularity_score"),)

    cluster_id = Column(
        Integer,
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    destination_id = Column(
        String(255),
        ForeignKey("destinations.place_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    popularity_score = Column(Float, nullable=True, index=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    cluster = relationship("Cluster", back_populates="destinations")
    destination = relationship("Destination", back_populates="cluster_destinations")


class Preference(Base):
    __tablename__ = "preferences"
    __table_args__ = (
        Index("ix_preference_cluster", "cluster_id"),
        Index("ix_preference_updated", "last_updated"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    weather_pref = Column(JSON, nullable=True)  # e.g. {"min_temp": 20, "max_temp": 30}
    attraction_types = Column(
        JSON, nullable=True
    )  # e.g. ["beach", "museum", "mountain"]
    budget_range = Column(JSON, nullable=True)  # e.g. {"min": 200, "max": 1000}
    kids_friendly = Column(Boolean, default=False)
    visited_destinations = Column(
        JSON, nullable=True
    )  # list of destination IDs or names

    embedding = Column(JSON, nullable=True)
    weight = Column(Float, default=1.0)
    cluster_id = Column(
        Integer, ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True
    )
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preference")
    cluster = relationship("Cluster", back_populates="preferences")
