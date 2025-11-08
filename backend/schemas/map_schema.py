from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any

class LocationCoordinates(BaseModel):
    """Tọa độ địa lý"""
    lat: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    lng: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")

class SearchSuggestion(BaseModel):
    """1 suggestion từ autocomplete"""
    place_id: str = Field(..., description="Google Place ID")
    description: str = Field(..., description="Mô tả đầy đủ")
    main_text: str = Field(..., description="Text chính (tên địa điểm)")
    secondary_text: str = Field(..., description="Text phụ (địa chỉ)")
    types: List[str] = Field(..., description="Các loại địa điểm")
    distance_meters: Optional[int] = Field(None, description="Khoảng cách từ user location")

class SearchLocationRequest(BaseModel):
    """Request cho search_location"""
    query: str = Field(..., min_length=2, description="Text tìm kiếm")
    user_lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude user")
    user_lng: Optional[float] = Field(None, ge=-180, le=180, description="Longitude user")
    radius: Optional[int] = Field(None, ge=100, le=50000, description="Bán kính (100-50000m)")
    place_types: Optional[str] = Field(None, description="Loại địa điểm")
    language: str = Field("vi", description="Ngôn ngữ")
    
    @validator('user_lng')
    def validate_location_pair(cls, lng, values):
        """Validate rằng nếu có lat thì phải có lng và ngược lại"""
        lat = values.get('user_lat')
        if (lat is None) != (lng is None):
            raise ValueError("user_lat và user_lng phải cùng có hoặc cùng không có")
        return lng
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Hồ Hoàn Kiếm",
                "user_lat": 21.0285,
                "user_lng": 105.8542,
                "radius": 5000,
                "language": "vi"
            }
        }

class SearchLocationResponse(BaseModel):
    """Response từ search_location"""
    status: str = Field(..., description="Status: OK")
    query: str = Field(..., description="Query gốc")
    suggestions: List[SearchSuggestion] = Field(..., description="List suggestions")
    total_results: int = Field(..., description="Số lượng kết quả")
    user_location: Optional[LocationCoordinates] = Field(None, description="Vị trí user")

class PhotoInfo(BaseModel):
    """Thông tin 1 photo"""
    photo_reference: str = Field(..., description="Reference để lấy photo")
    width: int = Field(..., description="Chiều rộng")
    height: int = Field(..., description="Chiều cao")

class OpeningHours(BaseModel):
    """Giờ mở cửa"""
    open_now: Optional[bool] = Field(None, description="Đang mở cửa không")
    weekday_text: Optional[List[str]] = Field(None, description="Text mô tả từng ngày")

class PlaceDetailsResponse(BaseModel):
    """Response từ get_location_details"""
    status: str = Field(..., description="Status: OK")
    place_id: str = Field(..., description="Google Place ID")
    name: str = Field(..., description="Tên địa điểm")
    formatted_address: str = Field(..., description="Địa chỉ đầy đủ")
    location: LocationCoordinates = Field(..., description="Tọa độ")
    rating: Optional[float] = Field(None, description="Rating (0-5)")
    phone: Optional[str] = Field(None, description="Số điện thoại")
    website: Optional[str] = Field(None, description="Website")
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="Giờ mở cửa")
    photos: List[PhotoInfo] = Field(default=[], description="Danh sách photos (max 5)")
    types: List[str] = Field(..., description="Các loại địa điểm")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "OK",
                "place_id": "ChIJ...",
                "name": "Hồ Hoàn Kiếm",
                "formatted_address": "Đinh Tiên Hoàng, Hoàn Kiếm, Hà Nội",
                "location": {"lat": 21.0288, "lng": 105.8525},
                "rating": 4.6,
                "types": ["tourist_attraction", "point_of_interest"]
            }
        }
