from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any, Tuple

class SearchSuggestion(BaseModel):
    place_id: str = Field(..., description="Google Place ID")
    description: str = Field(..., description="Mô tả đầy đủ")
    main_text: str = Field(..., description="Text chính (tên địa điểm)")
    secondary_text: str = Field(..., description="Text phụ (địa chỉ)")
    types: List[str] = Field(..., description="Các loại địa điểm")
    distance_meters: Optional[int] = Field(None, description="Khoảng cách từ user location")

class SearchLocationRequest(BaseModel):
    """Request cho search_location"""
    query: str = Field(..., min_length=2, description="Text search")
    user_location: Optional[Tuple[float, float]] = Field(None, description="Tọa độ user (lat, lng)")
    radius: Optional[int] = Field(None, ge=100, le=50000, description="Bán kính (100-50000m)")
    place_types: Optional[str] = Field(None, description="Loại địa điểm")
    language: str = Field("vi", description="Ngôn ngữ")

    @validator('user_location')
    def validate_location_pair(cls, user_location):
        if user_location is not None:
            lat, lng = user_location
            if lat is None or lng is None:
                raise ValueError("user_location phải có cả lat và lng")
        return user_location

class SearchLocationResponse(BaseModel):
    status: str = Field(..., description="Status: OK")
    query: str = Field(..., description="Query gốc")
    suggestions: List[SearchSuggestion] = Field(..., description="List suggestions")

class PhotoInfo(BaseModel):
    photo_reference: str = Field(..., description="Reference để get photo")
    width: int = Field(..., description="Chiều rộng")
    height: int = Field(..., description="Chiều cao")

class OpeningHours(BaseModel):
    open_now: Optional[bool] = Field(None, description="Đang mở cửa không")
    weekday_text: Optional[List[str]] = Field(None, description="Text mô tả từng ngày")

class PlaceDetailsResponse(BaseModel):
    status: str = Field(..., description="Status: OK")
    place_id: str = Field(..., description="Google Place ID")
    name: str = Field(..., description="Tên địa điểm")
    formatted_address: str = Field(..., description="Địa chỉ đầy đủ")
    location: Tuple[float, float] = Field(..., description="Tọa độ (lat, lng)")
    rating: Optional[float] = Field(None, description="Rating (0-5)")
    phone: Optional[str] = Field(None, description="Số điện thoại")
    website: Optional[str] = Field(None, description="Website")
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="Giờ mở cửa")
    photos: List[PhotoInfo] = Field(default=[], description="Danh sách photos (max 5)")
    types: List[str] = Field(..., description="Các loại địa điểm")