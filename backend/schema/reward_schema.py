from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class EnvironmentProtectionAction(str, Enum):
    carbon_footprint = "carbon_footprint"
    garbage_classification = "garbage_classification"
    recycling = "recycling"
    tree_planting = "tree_planting"
    nature_conservation = "nature_conservation"

class RewardType(str, Enum):
    eco_point = "eco_point"
    badge = "badge"
    rank = "rank"

class RewardAction(str, Enum):
    register = "register"
    eco_trip = "eco_trip"
    forum_post = "forum_post"
    environment_protection = "environment_protection"
    daily_login = "daily_login"
    referral = "referral"

class RewardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    reward_type: RewardType
    action_trigger: RewardAction
    environment_protection_action: Optional[EnvironmentProtectionAction] = None
    value: Optional[int] = 0

class RewardResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    reward_type: RewardType
    action_trigger: RewardAction
    environment_protection_action: Optional[EnvironmentProtectionAction]
    value: Optional[int]
    
    model_config = {
        "from_attributes": True
    }

class UserRewardResponse(BaseModel):
    user_id: int
    rewards: List[RewardResponse]
    total_point: Optional[int] = 0

    model_config = {
        "from_attributes": True
    }
