from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional, List

class DestinationCreate(BaseModel):
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)

class DestinationUpdate(BaseModel):
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    
    
class UserSavedDestinationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    destination_id: int = Field(..., gt=0)
    
class UserSavedDestinationResponse(BaseModel):
    id: int
    user_id: int
    destination_id: int

    model_config = ConfigDict(from_attributes=True)