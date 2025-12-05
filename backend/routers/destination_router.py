from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database.db import get_db
from models.destination import GreenVerifiedStatus
from models.user import Activity
from schemas.destination_schema import (
    DestinationResponse,
    DestinationUpdate,
    UserSavedDestinationResponse,
)
from schemas.message_schema import CommonMessageResponse
from schemas.user_schema import (
    UserActivityCreate,
)
from services.destination_service import DestinationService
from services.user_service import UserService
from utils.token.authentication_util import get_current_user
from utils.token.authorizer import require_roles

router = APIRouter(prefix="/destinations", tags=["Destinations"])


@router.post(
    "/saved/{destination_id}",
    response_model=UserSavedDestinationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_destination_for_current_user(
    destination_id: str = Path(..., min_length=1),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await DestinationService.save_destination_for_user(
        user_db, current_user["user_id"], destination_id
    )
    activity_data = UserActivityCreate(
        activity=Activity.save_destination, destination_id=destination_id
    )
    await UserService.log_user_activity(user_db, current_user["user_id"], activity_data)
    return result


@router.get(
    "/saved/me/all",
    response_model=list[UserSavedDestinationResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_saved_destinations(
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await DestinationService.get_saved_destinations_for_user(
        user_db, current_user["user_id"]
    )


@router.delete(
    "/saved/{destination_id}",
    response_model=CommonMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def unsave_destination_for_current_user(
    destination_id: str = Path(...),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await DestinationService.delete_saved_destination(
        user_db, current_user["user_id"], destination_id
    )


# Admin endpoints
@router.get(
    "/admin/all",
    response_model=list[DestinationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all destinations (Admin only)",
    dependencies=[Depends(require_roles(["Admin"]))],
)
async def admin_get_all_destinations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    verified_status: Optional[GreenVerifiedStatus] = Query(None),
    user_db: AsyncSession = Depends(get_db),
):
    """Get all destinations with optional filtering by verification status. Admin only."""
    return await DestinationService.get_all_destinations(
        user_db, skip=skip, limit=limit, verified_status=verified_status
    )


@router.put(
    "/admin/{destination_id}/certificate",
    response_model=DestinationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update destination certificate status (Admin only)",
    dependencies=[Depends(require_roles(["Admin"]))],
)
async def admin_update_certificate(
    destination_id: str = Path(...),
    new_status: GreenVerifiedStatus = Query(...),
    user_db: AsyncSession = Depends(get_db),
):
    """Manually update the green verification certificate of a destination. Admin only."""
    update_data = DestinationUpdate(green_verified_status=new_status)
    return await DestinationService.update_destination(user_db, destination_id, update_data)
