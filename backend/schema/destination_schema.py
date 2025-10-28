from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class DestinationCreate(BaseModel):
    longitude: float
    latitude: float

class DestinationUpdate(BaseModel):
    longitude: Optional[float] = None
    latitude: Optional[float] = None