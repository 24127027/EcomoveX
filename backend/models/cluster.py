from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from database.user_database import UserBase
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)

class Cluster(UserBase):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    algorithm = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
class UserClusterAssociation(UserBase):
    __tablename__ = "user_cluster_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    # score = Column(Float, nullable=False) # Optional: score indicating strength of association
    
    user = relationship("User", back_populates="clusters")
    cluster = relationship("Cluster")
    
class ClusterDestination(UserBase):
    __tablename__ = "cluster_destinations"
    
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(Integer, nullable=False)  # No FK - destination in separate DB
    popularity_score = Column(Float, nullable=True)
    
    cluster = relationship("Cluster")