from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.destination_database import get_destination_db
from database.user_database import get_user_db
from schemas.destination_schema import UserSavedDestinationResponse
from schemas.user_schema import UserActivityCreate
from services.destination_service import DestinationService, UserSavedDestinationService
from services.user_service import UserActivityService
from utils.authentication_util import get_current_user
from models.user import Activity

router = APIRouter(prefix="/destinations", tags=["Destinations"])

@router.post("/saved/{destination_id}", response_model=UserSavedDestinationResponse, status_code=status.HTTP_201_CREATED)
async def save_destination_for_current_user(
    destination_id: int = Path(..., gt=0, description="Destination ID to save"),
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    result = await UserSavedDestinationService.save_destination_for_user(
        user_db, 
        current_user["user_id"], 
        destination_id
    )
    activity_data = UserActivityCreate(
        activity_type=Activity.save_destination,
        destination_id=destination_id
    )
    await UserActivityService.log_user_activity(user_db, current_user["user_id"], activity_data)    
    return result

@router.get("/saved/me/all", response_model=list[UserSavedDestinationResponse], status_code=status.HTTP_200_OK)
async def get_my_saved_destinations(
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await UserSavedDestinationService.get_saved_destinations_for_user(
        user_db, 
        current_user["user_id"]
    )

@router.delete("/saved/{destination_id}", status_code=status.HTTP_200_OK)
async def unsave_destination_for_current_user(
    destination_id: int = Path(..., gt=0, description="Destination ID to unsave"),
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await UserSavedDestinationService.delete_saved_destination(
        user_db, 
        current_user["user_id"], 
        destination_id
    )