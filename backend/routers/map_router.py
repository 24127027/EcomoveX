from typing import List
from fastapi import APIRouter, Depends, Path, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import *
from database.db import get_db
from schemas.map_schema import *
from schemas.user_schema import *
from schemas.air_schema import *
from services.map_service import mapService
from services.user_service import UserActivityService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/map", tags=["Map & Navigation"])

@router.post("/search", response_model=AutocompleteResponse, status_code=status.HTTP_200_OK)
async def search_location(
    request: SearchLocationRequest,
    user_db: AsyncSession = Depends(get_db)
):
    result = await mapService.search_location(user_db, request)
    return result

@router.get("/place/{place_id}", response_model=PlaceDetailsResponse, status_code=status.HTTP_200_OK)
async def get_place_details(
    place_id: str = Path(..., min_length=1),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await mapService.get_location_details(
        place_id=place_id,
    )
    
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
    location = (lat, lng)
    result = await mapService.reverse_geocode(location=location)
    return result