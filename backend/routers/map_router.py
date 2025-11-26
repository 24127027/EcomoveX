from typing import Tuple
from fastapi import APIRouter, Depends, Path, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.route_schema import DirectionsResponse
from models.user import *
from database.db import get_db
from schemas.map_schema import *
from schemas.destination_schema import Location
from schemas.user_schema import *
from schemas.air_schema import *
from services.map_service import mapService
from services.user_service import UserActivityService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/map", tags=["Map & Navigation"])

@router.post("/text-search", response_model=TextSearchResponse, status_code=status.HTTP_200_OK)
async def text_search_place(
    request: TextSearchRequest,
    user_db: AsyncSession = Depends(get_db)
):
    result = await mapService.text_search_place(user_db, request)
    return result

@router.post("/autocomplete", response_model=AutocompleteResponse, status_code=status.HTTP_200_OK)
async def autocomplete(
    request: AutocompleteRequest,
    user_db: AsyncSession = Depends(get_db)
):
    result = await mapService.autocomplete(user_db, request)
    return result

@router.get("/place/{place_id}", response_model=PlaceDetailsResponse, status_code=status.HTTP_200_OK)
async def get_place_details(
    place_id: str = Path(..., min_length=1),
    session_token: Optional[str] = Query(None),
    categories: List[PlaceDataCategory] = Query(
        default=[PlaceDataCategory.BASIC]
    ),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    request_data = PlaceDetailsRequest(
        place_id=place_id,
        session_token=session_token,
        categories=categories
    )

    result = await mapService.get_location_details(request_data)
    
    activity_data = UserActivityCreate(
        activity=Activity.search_destination,
        destination_id=place_id
    )
    await UserActivityService.log_user_activity(user_db, current_user["user_id"], activity_data)
    
    return result

@router.post("/geocode", response_model=GeocodingResponse, status_code=status.HTTP_200_OK)
async def geocode_address(
    address: str = Body(..., min_length=2),
):
    result = await mapService.geocode_address(address=address)
    return result

@router.post("/reverse-geocode", response_model=GeocodingResponse, status_code=status.HTTP_200_OK)
async def reverse_geocode(
    lat: float = Body(..., ge=-90.0, le=90.0),
    lng: float = Body(..., ge=-180.0, le=180.0)
):    
    location = Location(latitude=lat, longitude=lng)
    result = await mapService.reverse_geocode(location=location)
    return result

@router.post("/search-along-route", response_model=SearchAlongRouteResponse, status_code=status.HTTP_200_OK)
async def search_along_route(
    direction_data: DirectionsResponse = Body(...),
    search_type: str = Body(..., min_length=2),
):
    result = await mapService.search_along_route(
        directions=direction_data,
        search_type=search_type,
    )
    return result