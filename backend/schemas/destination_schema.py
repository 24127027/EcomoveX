from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List

class DestinationCreate(BaseModel):
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)

class DestinationUpdate(BaseModel):
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    latitude: Optional[float] = Field(None, ge=-90, le=90)