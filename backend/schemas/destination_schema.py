from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from models.destination import GreenVerifiedStatus

class DestinationCreate(BaseModel):
    place_id: str
    green_verified_status: Optional[GreenVerifiedStatus] = None 

class DestinationUpdate(BaseModel):
    green_verified_status: Optional[GreenVerifiedStatus] = None
    
class UserSavedDestinationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    destination_id: str = Field(..., min_length=1)
    
class UserSavedDestinationResponse(BaseModel):
    user_id: int
    destination_id: str
    saved_at: datetime

    model_config = ConfigDict(from_attributes=True)