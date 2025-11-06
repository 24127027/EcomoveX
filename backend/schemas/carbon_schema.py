from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from models.carbon import VehicleType, FuelType

class CarbonEmissionCreate(BaseModel):
    vehicle_type: VehicleType
    distance_km: float = Field(..., gt=0)
    fuel_type: FuelType

class CarbonEmissionUpdate(BaseModel):
    vehicle_type: VehicleType | None = None
    distance_km: float | None = Field(None, gt=0)
    fuel_type: FuelType | None = None

class CarbonEmissionResponse(BaseModel):
    emission_id: int = Field(alias="id")
    user_id: int
    vehicle_type: VehicleType
    distance_km: float
    fuel_type: FuelType
    carbon_emission_kg: float
    calculated_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }