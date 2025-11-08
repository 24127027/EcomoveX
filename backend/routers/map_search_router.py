from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from services.map_service import MapService
from schemas.carbon_schema import SearchLocationResponse, PlaceDetailsResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/map", tags=["Map Search"])

class SearchLocationRequest(BaseModel):
    """Request body cho search location"""
    query: str = Field(..., min_length=2, description="Text tìm kiếm (tối thiểu 2 ký tự)")
    user_lat: Optional[float] = Field(None, description="Vĩ độ vị trí hiện tại của user")
    user_lng: Optional[float] = Field(None, description="Kinh độ vị trí hiện tại của user")
    radius: Optional[int] = Field(None, ge=100, le=50000, description="Bán kính tìm kiếm (meters, 100-50000)")
    place_types: Optional[str] = Field(None, description="Loại địa điểm: geocode, address, establishment, (regions), (cities)")
    language: str = Field("vi", description="Ngôn ngữ kết quả")
    
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

@router.post(
    "/search",
    response_model=SearchLocationResponse,
    summary="🔍 Search Bar - Tìm kiếm địa điểm",
    description="""
    Tính năng Search Bar giống Google Maps.
    
    **Cách sử dụng:**
    1. User gõ text vào search bar (vd: "Hồ Hoàn Kiếm", "Nhà hàng gần đây", "123 Trần Duy Hưng")
    2. API trả về list suggestions với autocomplete
    3. User chọn 1 suggestion từ list
    4. Gọi API `/map/place/{place_id}` để lấy chi tiết
    
    **Features:**
    - ✅ Autocomplete real-time
    - ✅ Ưu tiên kết quả gần user location
    - ✅ Hỗ trợ tìm địa chỉ, địa điểm, cơ sở kinh doanh
    - ✅ Tìm kiếm theo bán kính
    - ✅ Đa ngôn ngữ (vi/en)
    
    **Place Types:**
    - `geocode`: Tìm địa chỉ
    - `address`: Tìm địa chỉ cụ thể
    - `establishment`: Tìm cơ sở kinh doanh (nhà hàng, khách sạn, etc.)
    - `(regions)`: Tìm vùng/khu vực
    - `(cities)`: Tìm thành phố
    """
)
async def search_location(request: SearchLocationRequest):
    """
    Search địa điểm với autocomplete suggestions
    
    Returns list suggestions khi user đang gõ
    """
    user_location = None
    if request.user_lat is not None and request.user_lng is not None:
        user_location = (request.user_lat, request.user_lng)
    
    result = await MapService.search_location(
        input_text=request.query,
        user_location=user_location,
        search_radius=request.radius,
        place_types=request.place_types,
        language=request.language
    )
    
    return result

@router.get(
    "/place/{place_id}",
    response_model=PlaceDetailsResponse,
    summary="📋 Lấy chi tiết địa điểm",
    description="""
    Lấy thông tin chi tiết của địa điểm sau khi user chọn từ search suggestions.
    
    **Response bao gồm:**
    - ✅ Tên địa điểm
    - ✅ Địa chỉ đầy đủ
    - ✅ Tọa độ (lat, lng)
    - ✅ Rating
    - ✅ Số điện thoại
    - ✅ Website
    - ✅ Giờ mở cửa
    - ✅ Photos (tối đa 5)
    - ✅ Loại địa điểm
    """
)
async def get_place_details(
    place_id: str,
    language: str = Query("vi", description="Ngôn ngữ (vi/en)")
):
    """
    Get chi tiết đầy đủ của place_id
    
    place_id lấy từ search suggestions
    """
    result = await MapService.get_location_details(
        place_id=place_id,
        language=language
    )
    
    return result

@router.get(
    "/search-simple",
    response_model=SearchLocationResponse,
    summary="🔍 Search đơn giản (GET method)",
    description="""
    Alternative endpoint dùng GET method cho search đơn giản.
    
    Dùng khi chỉ cần search nhanh không cần user location.
    """
)
async def search_location_simple(
    q: str = Query(..., min_length=2, description="Text tìm kiếm"),
    lat: Optional[float] = Query(None, description="Latitude của user"),
    lng: Optional[float] = Query(None, description="Longitude của user"),
    radius: Optional[int] = Query(None, ge=100, le=50000, description="Bán kính (meters)"),
    types: Optional[str] = Query(None, description="Loại địa điểm"),
    lang: str = Query("vi", description="Ngôn ngữ")
):
    """
    GET method search - đơn giản hơn, dùng query parameters
    
    Example: /map/search-simple?q=Hồ Hoàn Kiếm&lat=21.0285&lng=105.8542
    """
    user_location = None
    if lat is not None and lng is not None:
        user_location = (lat, lng)
    
    result = await MapService.search_location(
        input_text=q,
        user_location=user_location,
        search_radius=radius,
        place_types=types,
        language=lang
    )
    
    return result
