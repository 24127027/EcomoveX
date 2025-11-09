from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from services.map_service import MapService
from schemas.map_schema import SearchLocationRequest, SearchLocationResponse, PlaceDetailsResponse
from pydantic import BaseModel, Field
from database.destination_database import get_destination_db

router = APIRouter(prefix="/map", tags=["Map Search"])

@router.post("/search", response_model=SearchLocationResponse, status_code=status.HTTP_200_OK)
async def search_location(request: SearchLocationRequest, db: AsyncSession = Depends(get_destination_db)):
    user_location = None
    if request.user_lat is not None and request.user_lng is not None:
        user_location = request.user_location
    result = await MapService.search_location(db=db, request=request)
    return result

@router.get("/place/{place_id}", response_model=PlaceDetailsResponse, status_code=status.HTTP_200_OK)
async def get_place_details(
    place_id: str,
    language: str = Query("vi")
):
    result = await MapService.get_location_details(
        place_id=place_id,
        language=language
    )
    
    return result