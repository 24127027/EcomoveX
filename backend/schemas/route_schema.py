from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any

class TransitStep(BaseModel):
    """Thông tin 1 bước đi xe công cộng"""
    line: str = Field(..., description="Số xe (vd: '86', 'Line 2A')")
    vehicle: str = Field(..., description="Loại xe: BUS, SUBWAY, TRAIN")
    departure_stop: str = Field(..., description="Trạm xuất phát")
    arrival_stop: str = Field(..., description="Trạm đến")
    num_stops: int = Field(..., description="Số trạm dừng")
    duration: str = Field(..., description="Thời gian (text)")

class WalkingStep(BaseModel):
    """Thông tin 1 bước đi bộ"""
    distance: str = Field(..., description="Khoảng cách (text)")
    duration: str = Field(..., description="Thời gian (text)")
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
    duration_in_traffic_min: float = Field(..., description="Thời gian có traffic (phút)")
    traffic_delay_min: float = Field(..., description="Thời gian delay do traffic (phút)")
    traffic_multiplier: Optional[float] = Field(None, description="Nhân tử tăng carbon")
    emission_increase_percent: Optional[float] = Field(None, description="% tăng carbon")

class RouteData(BaseModel):
    """Dữ liệu 1 route option"""
    type: str = Field(..., description="Loại route: fastest_driving, transit, walking, etc.")
    mode: str = Field(..., description="Mode: driving, transit, walking, bicycling")
    display_name: str = Field(..., description="Tên hiển thị")
    distance_km: float = Field(..., description="Khoảng cách (km)")
    duration_min: float = Field(..., description="Thời gian (phút)")
    duration_text: str = Field(..., description="Thời gian (text)")
    carbon_kg: float = Field(..., description="CO2 emission (kg)")
    carbon_grams: float = Field(..., description="CO2 emission (gram)")
    emission_factor: float = Field(..., description="Hệ số phát thải")
    route_details: Dict[str, Any] = Field(..., description="Full Google Maps route data")
    priority_score: float = Field(..., description="Score để sắp xếp")
    has_traffic_data: bool = Field(..., description="Có dữ liệu traffic không")
    traffic_info: Optional[TrafficInfo] = Field(None, description="Thông tin traffic")
    transit_info: Optional[TransitDetails] = Field(None, description="Chi tiết xe công cộng")
    reason: Optional[str] = Field(None, description="Lý do chọn route này")

class TimeComparison(BaseModel):
    """So sánh thời gian với fastest route"""
    vs_fastest_min: float = Field(..., description="Chênh lệch thời gian (phút)")
    vs_fastest_percent: float = Field(..., description="Chênh lệch thời gian (%)")

class CarbonComparison(BaseModel):
    """So sánh carbon với driving"""
    vs_driving_kg: float = Field(..., description="Tiết kiệm CO2 (kg)")
    vs_driving_percent: float = Field(..., description="Tiết kiệm CO2 (%)")

class SmartRouteData(RouteData):
    """Smart route với thêm comparison data"""
    time_comparison: Optional[TimeComparison] = None
    carbon_comparison: Optional[CarbonComparison] = None

class Recommendation(BaseModel):
    """Recommendation cho user"""
    route: str = Field(..., description="Route được recommend: fastest, lowest_carbon, smart_combination")
    reason: str = Field(..., description="Lý do recommend")

class FindRoutesRequest(BaseModel):
    """Request cho find_three_optimal_routes"""
    origin: str = Field(..., min_length=1, description="Điểm xuất phát")
    destination: str = Field(..., min_length=1, description="Điểm đến")
    max_time_ratio: float = Field(1.3, ge=1.0, le=3.0, description="Chấp nhận chậm hơn bao nhiêu lần (1.0-3.0)")
    language: str = Field("vi", description="Ngôn ngữ: vi hoặc en")
    
    class Config:
        json_schema_extra = {
            "example": {
                "origin": "Hà Nội",
                "destination": "Nội Bài International Airport",
                "max_time_ratio": 1.3,
                "language": "vi"
            }
        }

class FindRoutesResponse(BaseModel):
    """Response từ find_three_optimal_routes"""
    status: str = Field(..., description="Status: OK hoặc error")
    origin: str = Field(..., description="Điểm xuất phát")
    destination: str = Field(..., description="Điểm đến")
    total_routes_analyzed: int = Field(..., description="Tổng số routes phân tích")
    routes: Dict[str, RouteData] = Field(..., description="3 routes tối ưu: fastest, lowest_carbon, smart_combination")
    recommendation: Recommendation = Field(..., description="Recommendation cho user")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "OK",
                "origin": "Hà Nội",
                "destination": "Nội Bài Airport",
                "total_routes_analyzed": 5,
                "routes": {
                    "fastest": {"type": "fastest_driving", "duration_min": 35.2, "carbon_kg": 5.59},
                    "lowest_carbon": {"type": "transit", "duration_min": 55.8, "carbon_kg": 1.02},
                    "smart_combination": {"type": "transit", "duration_min": 55.8, "carbon_kg": 1.02}
                },
                "recommendation": {"route": "smart_combination", "reason": "Good balance"}
            }
        }
