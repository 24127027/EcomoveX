from fastapi import APIRouter, Depends, Query, status

from schemas.green_verification_schema import (
    GreenVerificationRequest,
    GreenVerificationResponse,
    ImageVerificationResult,
)
from services.green_verification_service import GreenVerificationService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/green-verification", tags=["Green Verification"])


@router.post(
    "/verify-batch",
    response_model=GreenVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify green coverage for multiple images",
)
async def verify_images_batch(
    request: GreenVerificationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Verify green coverage for a batch of image URLs using segmentation and depth analysis.

    Process:
    1. Vegetation segmentation using YOLO model
    2. Depth estimation using MiDaS
    3. Calculate green proportion (vegetation pixels / total pixels)
    4. Calculate depth-weighted score (closer vegetation = higher score)
    5. Compute final green score = proportion × depth_weighted
    6. Verify against threshold

    Returns individual results for each image plus summary statistics.
    """
    return await GreenVerificationService.verify_images(request)


@router.get(
    "/verify",
    response_model=ImageVerificationResult,
    status_code=status.HTTP_200_OK,
    summary="Verify green coverage for a single image",
)
async def verify_single_image(
    image_url: str = Query(..., description="URL of the image to verify"),
    green_threshold: float = Query(
        0.3, ge=0.0, le=1.0, description="Threshold for green verification"
    ),
    current_user: dict = Depends(get_current_user),
):
    """
    Verify green coverage for a single image URL.

    Process:
    1. Vegetation segmentation using YOLO model
    2. Depth estimation using MiDaS
    3. Calculate green proportion and depth-weighted score
    4. Verify against threshold

    Returns verification result with scores and verification status.
    """
    return await GreenVerificationService.verify_single_image(
        image_url, green_threshold
    )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check green verification service health",
)
async def health_check():
    """
    Check if the green verification service is ready.

    Returns status of segmentation and depth models.
    """
    try:
        orchestrator = GreenVerificationService.get_orchestrator()
        return {
            "status": "healthy",
            "segmentation_model": "loaded",
            "depth_model": "loaded",
            "device": str(orchestrator.device),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
