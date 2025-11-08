from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from models.route import TransportMode, RouteType

# Repository schemas
class RouteCreate(BaseModel):
    """Schema for creating a new route record"""
    user_id: int = Field(..., description="User ID")
    origin_id: int = Field(..., description="Origin destination ID")
    destination_id: int = Field(..., description="Destination ID")
    distance_km: float = Field(..., ge=0, description="Distance in kilometers")
    estimated_travel_time_min: float = Field(..., ge=0, description="Travel time in minutes")
    carbon_emission_kg: float = Field(..., ge=0, description="Carbon emission in kg")

class RouteUpdate(BaseModel):
    """Schema for updating a route record"""
    distance_km: Optional[float] = Field(None, ge=0, description="Distance in kilometers")
    estimated_travel_time_min: Optional[float] = Field(None, ge=0, description="Travel time in minutes")
    carbon_emission_kg: Optional[float] = Field(None, ge=0, description="Carbon emission in kg")

class RouteResponse(BaseModel):
    """Schema for route response"""
    user_id: int
    origin_id: int
    destination_id: int
    distance_km: float
    estimated_travel_time_min: float
    carbon_emission_kg: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TransitStep(BaseModel):
    line: str = Field(..., description="Số xe (vd: '86', 'Line 2A')")
    vehicle: TransportMode = Field(..., description="Loại xe: BUS, SUBWAY, TRAIN")
    departure_stop: Dict[str, float] = Field(..., description="Trạm xuất phát")
    arrival_stop: Dict[str, float] = Field(..., description="Trạm đến")
    num_stops: int = Field(..., description="Số trạm dừng")
    duration: float = Field(..., description="Thời gian (minutes)")

class WalkingStep(BaseModel):
    distance: float = Field(..., description="Khoảng cách (meters)")
    duration: float = Field(..., description="Thời gian (minutes)")
    instruction: str = Field(..., description="Hướng dẫn HTML")

class TransitDetails(BaseModel):
    transit_steps: List[TransitStep] = Field(..., description="Các bước đi xe")
    walking_steps: List[WalkingStep] = Field(..., description="Các bước đi bộ")
    total_transit_steps: int = Field(..., description="Tổng số bước đi xe")
    total_walking_steps: int = Field(..., description="Tổng số bước đi bộ")

class RouteData(BaseModel):
    type: str = Field(..., description="Loại route: fastest_driving, transit, walking, etc.")
    mode: List[TransportMode] = Field(..., description="Mode: driving, transit, walking, bicycling")
    distance: float = Field(..., description="Khoảng cách (km)")
    duration: float = Field(..., description="Thời gian (phút)")
    carbon: float = Field(..., description="CO2 emission (kg)")
    route_details: Dict[str, Any] = Field(..., description="Full Google Maps route data")
    transit_info: Optional[TransitDetails] = Field(None, description="Chi tiết xe công cộng")

class FindRoutesRequest(BaseModel):
    """Request cho find_three_optimal_routes"""
    origin: Tuple[float, float] = Field(..., description="Điểm xuất phát")
    destination: Tuple[float, float] = Field(..., description="Điểm đến")
    max_time_ratio: float = Field(1.3, ge=1.0, le=3.0, description="Chấp nhận chậm hơn bao nhiêu lần (1.0-3.0)")
    language: str = Field("vi", description="Ngôn ngữ: vi hoặc en")

class FindRoutesResponse(BaseModel):
    origin: Dict[str, float] = Field(..., description="Điểm xuất phát")
    destination: Dict[str, float] = Field(..., description="Điểm đến")
    routes: Dict[RouteType, RouteData] = Field(..., description="3 routes tối ưu: fastest, lowest_carbon, smart_combination")
    recommendation: str = Field(..., description="Recommendation cho user")
    
    model_config = ConfigDict(
        from_attributes=True,
    )