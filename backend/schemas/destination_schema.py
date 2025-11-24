from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Tuple
from datetime import datetime
from models.destination import GreenVerifiedStatus

class Location(BaseModel):
    longitude: float = Field(alias="lng")
    latitude: float = Field(alias="lat")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_tuples=False,
        
        json_schema_extra={"serialization": {"by_alias": True}}
    )
    
class Bounds(BaseModel):
    northeast: Location
    southwest: Location

class Geometry(BaseModel):
    location: Location
    bounds: Optional[Bounds] = None

class DestinationCreate(BaseModel):
    place_id: str = Field(..., alias="place_id")
    green_verified_status: Optional[GreenVerifiedStatus] = None 
    
    model_config = ConfigDict(populate_by_name=True)

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