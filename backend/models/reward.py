from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    users = relationship("UserReward", back_populates="reward")


class UserReward(Base):
    __tablename__ = "user_rewards"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reward_id = Column(Integer, ForeignKey("rewards.id", ondelete="CASCADE"), nullable=False)
    obtained_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "reward_id"),
    )

    user = relationship("User", back_populates="rewards")
    reward = relationship("Reward", back_populates="users")