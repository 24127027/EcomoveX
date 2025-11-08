from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class TransportMode(str, Enum):
    """Các phương thức di chuyển"""
    DRIVING = "driving"
    CAR = "car"
    MOTORBIKE = "motorbike"
    MOTORCYCLE = "motorcycle"
    TRANSIT = "transit"
    BUS = "bus"
    TRAIN = "train"
    SUBWAY = "subway"
    METRO = "metro"
    BICYCLING = "bicycling"
    BICYCLE = "bicycle"
    WALKING = "walking"
    WALK = "walk"
    TAXI = "taxi"
    GRAB = "grab"
    GRAB_CAR = "grab_car"
    GRAB_BIKE = "grab_bike"

class FuelType(str, Enum):
    """Loại nhiên liệu cho xe có động cơ"""
    PETROL = "petrol"
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    ELECTRIC = "electric"
    CNG = "cng"  # Compressed Natural Gas
    LPG = "lpg"  # Liquefied Petroleum Gas

class CalculateEmissionRequest(BaseModel):
    """Request cho calculate_emission_by_mode"""
    distance_km: float = Field(..., gt=0, description="Khoảng cách (km)")
    mode: TransportMode = Field(..., description="Phương thức di chuyển")
    fuel_type: Optional[FuelType] = Field(FuelType.PETROL, description="Loại nhiên liệu (mặc định: petrol)")
    passengers: int = Field(1, ge=1, description="Số hành khách")
    congestion_ratio: float = Field(1.0, ge=1.0, le=5.0, description="Tỷ lệ traffic (1.0-5.0)")
    use_realtime_grid: bool = Field(True, description="Dùng grid intensity real-time cho EV")
    
    class Config:
        json_schema_extra = {
            "example": {
                "distance_km": 15.5,
                "mode": "driving",
                "fuel_type": "petrol",
                "passengers": 1,
                "congestion_ratio": 1.5
            }
        }

class EmissionResult(BaseModel):
    """Response từ calculate_emission_by_mode"""
    distance_km: float = Field(..., description="Khoảng cách (km)")
    mode: str = Field(..., description="Mode được sử dụng (sau khi mapping)")
    fuel_type: Optional[str] = Field(None, description="Loại nhiên liệu được sử dụng")
    passengers: int = Field(..., description="Số hành khách")
    emission_factor_g_per_km: float = Field(..., description="Hệ số phát thải (gCO2/km)")
    total_co2_grams: float = Field(..., description="Tổng CO2 (gram)")
    total_co2_kg: float = Field(..., description="Tổng CO2 (kg)")
    per_passenger_co2_grams: float = Field(..., description="CO2 per passenger (gram)")
    per_passenger_co2_kg: float = Field(..., description="CO2 per passenger (kg)")
    grid_intensity_used: Optional[float] = Field(None, description="Grid intensity cho EV")
    data_source: str = Field(..., description="Nguồn dữ liệu")
    traffic_congestion_ratio: Optional[float] = Field(None, description="Tỷ lệ traffic")
    traffic_multiplier: Optional[float] = Field(None, description="Nhân tử traffic")
    emission_increase_percent: Optional[float] = Field(None, description="% tăng do traffic")
    
    class Config:
        json_schema_extra = {
            "example": {
                "distance_km": 15.5,
                "mode": "car_petrol",
                "passengers": 1,
                "emission_factor_g_per_km": 268.8,
                "total_co2_grams": 4166.4,
                "total_co2_kg": 4.166,
                "per_passenger_co2_grams": 4166.4,
                "per_passenger_co2_kg": 4.166,
                "data_source": "Vietnam-specific (Climatiq + Electricity Maps)",
                "traffic_congestion_ratio": 1.5,
                "traffic_multiplier": 1.4,
                "emission_increase_percent": 40.0
            }
        }

class CompareModesRequest(BaseModel):
    """Request cho compare_transport_modes"""
    distance_km: float = Field(..., gt=0, description="Khoảng cách (km)")
    modes: List[TransportMode] = Field(..., min_length=2, description="List các modes để so sánh")
    
    class Config:
        json_schema_extra = {
            "example": {
                "distance_km": 10.0,
                "modes": ["driving", "transit", "bicycling", "walking"]
            }
        }

class ModeComparison(BaseModel):
    """Kết quả so sánh 1 mode"""
    mode: str
    co2_kg: float

class CompareModesResponse(BaseModel):
    """Response từ compare_transport_modes"""
    distance_km: float
    modes: Dict[str, EmissionResult]
    best_option: ModeComparison
    worst_option: ModeComparison
    savings_potential_kg: float