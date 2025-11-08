from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional, List, Tuple
from models.destination import GreenVerifiedStatus

class DestinationCreate(BaseModel):
    place_id: str = Field(..., description="Google Place ID")
    green_verified_status: Optional[GreenVerifiedStatus] = None 

class DestinationUpdate(BaseModel):
    green_verified_status: Optional[GreenVerifiedStatus] = Field(None, description="Trạng thái xanh verified")
    
class UserSavedDestinationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    destination_id: int = Field(..., gt=0)
    
class UserSavedDestinationResponse(BaseModel):
    id: int
    user_id: int
    destination_id: int

    model_config = ConfigDict(from_attributes=True)