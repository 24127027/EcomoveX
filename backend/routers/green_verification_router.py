from fastapi import APIRouter, Depends, Query, status

from services.green_verification_service import GreenVerificationService
from schemas.green_verification_schema import GreenVerificationResponse
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/green-verification", tags=["Green Verification"])


@router.get(
    "/verify-place",
    response_model=GreenVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify green coverage for a place ID"
)
async def verify_place_green(
    place_id: str = Query(..., description="Place ID to verify"),
    current_user: dict = Depends(get_current_user),
):
    """
    Verify green coverage for an entire place using its place_id.

    Returns:
        - Aggregated green score (float)
        - Status (Green Certified / AI Green Verified / Not Green Verified)
    """
    return await GreenVerificationService.verify_place_green_coverage(place_id)
