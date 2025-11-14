from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from models.mission import RewardType, MissionAction

class MissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    reward_type: RewardType
    action_trigger: MissionAction
    value: Optional[int] = Field(0, ge=0)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Mission name cannot be empty or whitespace")
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip() if v else None

class MissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    reward_type: Optional[RewardType] = None
    action_trigger: Optional[MissionAction] = None
    value: Optional[int] = Field(None, ge=0)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Mission name cannot be empty or whitespace")
        return v.strip() if v else None

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip() if v else None

class MissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    reward_type: RewardType
    action_trigger: MissionAction
    value: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)

class UserRewardResponse(BaseModel):
    user_id: int
    missions: List[MissionResponse]
    total_point: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)