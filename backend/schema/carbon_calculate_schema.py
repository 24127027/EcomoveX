from pydantic import BaseModel, Field
from enum import Enum

class VehicleType(str, Enum):
    car = "car"
    bus = "bus"
    motorbike = "motorbike"
    walk_or_cycle = "walk or cycle"

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

    model_config = {
        "from_attributes": True
    }