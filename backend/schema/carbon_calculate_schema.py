from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class VehicleType(str, Enum):
    car = "car"
    bus = "bus"
    motorbike = "motorbike"
    bike = "bike"
    train = "train"
    airplane = "airplane"
    walk = "walk"

class FuelType(str, Enum):
    petrol = "petrol"
    diesel = "diesel"
    electric = "electric"
    hybrid = "hybrid"
    none = "none"

class CarbonCalculateRequest(BaseModel):
    vehicle_type: VehicleType
    distance_km: float = Field(..., gt=0, description="Distance traveled in kilometers")
    fuel_type: FuelType

class CarbonCalculateResponse(BaseModel):
    vehicle_type: VehicleType
    distance_km: float
    fuel_type: FuelType
    carbon_emission_kg: float

    class Config:
        orm_mode = True