from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from services.map_service import MapService
from schemas.carbon_schema import SearchLocationResponse, PlaceDetailsResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/map", tags=["Map Search"])

class SearchLocationRequest(BaseModel):
    """Request body cho search location"""
    query: str = Field(..., min_length=2, description="Text search (tối thiểu 2 ký tự)")
    user_lat: Optional[float] = Field(None, description="Vĩ độ vị trí hiện tại của user")
    user_lng: Optional[float] = Field(None, description="Kinh độ vị trí hiện tại của user")
    radius: Optional[int] = Field(None, ge=100, le=50000, description="Bán kính search (meters, 100-50000)")
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
)
async def search_location(request: SearchLocationRequest):
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
)
async def get_place_details(
    place_id: str,
    language: str = Query("vi", description="Ngôn ngữ (vi/en)")
):
    result = await MapService.get_location_details(
        place_id=place_id,
        language=language
    )
    
    return result

@router.get(
    "/search-simple",
    response_model=SearchLocationResponse,
    summary="🔍 Search đơn giản (GET method)",
)
async def search_location_simple(
    q: str = Query(..., min_length=2, description="Text search"),
    lat: Optional[float] = Query(None, description="Latitude của user"),
    lng: Optional[float] = Query(None, description="Longitude của user"),
    radius: Optional[int] = Query(None, ge=100, le=50000, description="Bán kính (meters)"),
    types: Optional[str] = Query(None, description="Loại địa điểm"),
    lang: str = Query("vi", description="Ngôn ngữ")
):
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