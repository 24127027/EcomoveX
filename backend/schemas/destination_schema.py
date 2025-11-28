from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Tuple, List
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
      
class UserSavedDestinationResponse(BaseModel):
    user_id: int
    destination_id: str
    saved_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DestinationEmbeddingCreate(BaseModel):
    destination_id: str = Field(..., min_length=1)
    embedding_vector: List[float] = Field(..., min_length=1)
    model_version: str = Field("v1", max_length=50)

class DestinationEmbeddingUpdate(BaseModel):
    embedding_vector: Optional[List[float]] = Field(None, min_length=1)
    model_version: Optional[str] = Field(None, max_length=50)

class DestinationEmbeddingResponse(BaseModel):
    destination_id: str
    embedding_vector: List[float]
    model_version: str

    model_config = ConfigDict(from_attributes=True)