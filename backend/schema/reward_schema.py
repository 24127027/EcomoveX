from pydantic import BaseModel
from typing import Optional, List
from models.mission import RewardType, MissionAction

class MissionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    reward_type: RewardType
    action_trigger: MissionAction
    value: Optional[int] = 0

class MissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    reward_type: Optional[RewardType] = None
    action_trigger: Optional[MissionAction] = None
    value: Optional[int] = None

class MissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    reward_type: RewardType
    action_trigger: MissionAction
    value: Optional[int]
    
    model_config = {
        "from_attributes": True
    }

class UserRewardResponse(BaseModel):
    user_id: int
    missions: List[MissionResponse]
    total_point: Optional[int] = 0

    model_config = {
        "from_attributes": True
    }