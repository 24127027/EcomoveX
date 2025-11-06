from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, PrimaryKeyConstraint
from database.user_database import UserBase
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
class Cluster(UserBase):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    algorithm = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("UserClusterAssociation", back_populates="cluster", cascade="all, delete-orphan")
    destinations = relationship("ClusterDestination", back_populates="cluster", cascade="all, delete-orphan")    

class UserClusterAssociation(UserBase):
    __tablename__ = "user_cluster_associations"
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'cluster_id'),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    # score = Column(Float, nullable=True) # Optional: score indicating user's affinity to the cluster

    user = relationship("User", back_populates="clusters")
    cluster = relationship("Cluster", back_populates="users")

class ClusterDestination(UserBase):
    __tablename__ = "cluster_destinations"
    
    __table_args__ = (
        PrimaryKeyConstraint('cluster_id', 'destination_id'),
    )

    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(Integer, nullable=False)  # No FK - destination in separate DB
    popularity_score = Column(Float, nullable=True)

    cluster = relationship("Cluster", back_populates="destinations")