from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from models.route import TransportMode, RouteType
from models.destination import Destination

class TransitStep(BaseModel):
    """Thông tin 1 bước đi xe công cộng"""
    line: str = Field(..., description="Số xe (vd: '86', 'Line 2A')")
    vehicle: TransportMode = Field(..., description="Loại xe: BUS, SUBWAY, TRAIN")
    departure_stop: Destination = Field(..., description="Trạm xuất phát")
    arrival_stop: Destination = Field(..., description="Trạm đến")
    num_stops: int = Field(..., description="Số trạm dừng")
    duration: float = Field(..., description="Thời gian (minutes)")

class WalkingStep(BaseModel):
    """Thông tin 1 bước đi bộ"""
    distance: float = Field(..., description="Khoảng cách (meters)")
    duration: float = Field(..., description="Thời gian (minutes)")
    instruction: str = Field(..., description="Hướng dẫn HTML")

class TransitDetails(BaseModel):
    """Chi tiết tuyến xe công cộng"""
    transit_steps: List[TransitStep] = Field(..., description="Các bước đi xe")
    walking_steps: List[WalkingStep] = Field(..., description="Các bước đi bộ")
    total_transit_steps: int = Field(..., description="Tổng số bước đi xe")
    total_walking_steps: int = Field(..., description="Tổng số bước đi bộ")

class TrafficInfo(BaseModel):
    """Thông tin traffic cho route"""
    congestion_ratio: float = Field(..., description="Tỷ lệ kẹt xe")
    duration_in_traffic: float = Field(..., description="Thời gian có traffic (phút)")
    traffic_delay: float = Field(..., description="Thời gian delay do traffic (phút)")

class RouteData(BaseModel):
    """Dữ liệu 1 route option"""
    type: str = Field(..., description="Loại route: fastest_driving, transit, walking, etc.")
    mode: List[TransportMode] = Field(..., description="Mode: driving, transit, walking, bicycling")
    distance: float = Field(..., description="Khoảng cách (km)")
    duration: float = Field(..., description="Thời gian (phút)")
    carbon: float = Field(..., description="CO2 emission (kg)")
    route_details: Any = Field(..., description="Full Google Maps route data")
    traffic_info: Optional[TrafficInfo] = Field(None, description="Thông tin traffic")
    transit_info: Optional[TransitDetails] = Field(None, description="Chi tiết xe công cộng")

class FindRoutesRequest(BaseModel):
    """Request cho find_three_optimal_routes"""
    origin: Destination = Field(..., description="Điểm xuất phát")
    destination: Destination = Field(..., description="Điểm đến")
    max_time_ratio: float = Field(1.3, ge=1.0, le=3.0, description="Chấp nhận chậm hơn bao nhiêu lần (1.0-3.0)")
    language: str = Field("vi", description="Ngôn ngữ: vi hoặc en")

class FindRoutesResponse(BaseModel):
    """Response từ find_three_optimal_routes"""
    origin: Destination = Field(..., description="Điểm xuất phát")
    destination: Destination = Field(..., description="Điểm đến")
    routes: Dict[RouteType, RouteData] = Field(..., description="3 routes tối ưu: fastest, lowest_carbon, smart_combination")
    recommendation: str = Field(..., description="Recommendation cho user")
    
    model_config = ConfigDict(
        from_attributes=True,
    )
