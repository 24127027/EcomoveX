from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from database.destination_database import get_destination_db
from database.user_database import get_user_db
from schemas.destination_schema import UserSavedDestinationResponse
from services.destination_service import DestinationService
from utils.authentication_util import get_current_user

router = APIRouter(prefix="/destinations", tags=["Destinations"])

@router.post("/saved/{destination_id}", response_model=UserSavedDestinationResponse)
async def save_destination_for_current_user(
    destination_id: int = Path(..., gt=0, description="Destination ID to save"),
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await DestinationService.save_destination_for_user(
        user_db, 
        current_user["user_id"], 
        destination_id
    )

@router.get("/saved/me/all")
async def get_my_saved_destinations(
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await DestinationService.get_saved_destinations_for_user(
        user_db, 
        current_user["user_id"]
    )

@router.delete("/saved/{destination_id}")
async def unsave_destination_for_current_user(
    destination_id: int = Path(..., gt=0, description="Destination ID to unsave"),
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await DestinationService.delete_saved_destination(
        user_db, 
        current_user["user_id"], 
        destination_id
    )

@router.get("/saved/check/{destination_id}")
async def check_if_destination_saved(
    destination_id: int = Path(..., gt=0, description="Destination ID to check"),
    user_db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    is_saved = await DestinationService.is_saved_destination(
        user_db, 
        current_user["user_id"], 
        destination_id
    )
    return {"destination_id": destination_id, "is_saved": is_saved}