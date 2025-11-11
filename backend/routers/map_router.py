from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import *
from database.destination_database import get_destination_db
from database.user_database import get_user_db
from schemas.map_schema import *
from schemas.user_schema import *
from services.map_service import MapService
from services.user_service import UserActivityService
from utils.authentication_util import get_current_user

router = APIRouter(prefix="/map", tags=["Map Search"])

@router.post("/search", response_model=SearchLocationResponse, status_code=status.HTTP_200_OK)
async def search_location(request: SearchLocationRequest, dest_db: AsyncSession = Depends(get_destination_db)):
    result = await MapService.search_location(dest_db, request)
    return result

@router.get("/place/{place_id}", response_model=PlaceDetailsResponse, status_code=status.HTTP_200_OK)
async def get_place_details(
    place_id: str,
    language: str = Query("vi"),
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    result = await MapService.get_location_details(
        place_id=place_id,
        language=language
    )
    
    activity_data = UserActivityCreate(
        activity_type=Activity.search_destination,
        destination_id=place_id
    )
    await UserActivityService.log_user_activity(user_db, current_user["user_id"], activity_data)
    
    return result