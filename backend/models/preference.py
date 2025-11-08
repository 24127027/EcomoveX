from sqlalchemy import Column, Integer, Float, Boolean, JSON, ForeignKey, DateTime
from database.preference_database import PreferenceBase
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)

class Preference(PreferenceBase):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # --- explicit user attributes ---
    weather_pref = Column(JSON, nullable=True)          # e.g. {"min_temp": 20, "max_temp": 30}
    attraction_types = Column(JSON, nullable=True)      # e.g. ["beach", "museum", "mountain"]
    budget_range = Column(JSON, nullable=True)          # e.g. {"min": 200, "max": 1000}
    kids_friendly = Column(Boolean, default=False)
    visited_destinations = Column(JSON, nullable=True)  # list of destination IDs or names

    # --- embedding and metadata ---
    embedding = Column(JSON, nullable=True)             # user preference vector
    weight = Column(Float, default=1.0)
    cluster_id = Column(Integer, ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True)
    last_updated = Column(DateTime, default=utc_now)

    # --- relationships ---
    user = relationship("User", back_populates="preference")
    cluster = relationship("Cluster", back_populates="preferences")
