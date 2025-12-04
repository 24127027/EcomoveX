from typing import List
from fastapi import APIRouter, Depends, Query, status

# Import Schema đã cập nhật
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
    summary="Verify green coverage and detect cups for multiple images"
)
async def verify_images_batch(
    request: GreenVerificationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Verify green coverage and detect recyclable cups for a batch of image URLs.
    
    Process:
    1. **Cup Detection:** Detect cups/glasses using YOLO and calculate normalized centroids (x/W, y/H).
    2. **Segmentation:** Vegetation segmentation using YOLO model.
    3. **Depth:** Depth estimation using MiDaS.
    4. **Scoring:** Calculate green proportion and depth-weighted score.
    5. **Verification:** Combine scores to verify green verification status.
    
    Returns:
        - Green scores (proportion, depth-weighted).
        - Verification status.
        - **Cup detections** (label, confidence, normalized coordinates).
    """
    return await GreenVerificationService.verify_images(request)


@router.get(
    "/verify",
    response_model=ImageVerificationResult,
    status_code=status.HTTP_200_OK,
    summary="Verify green coverage and detect cups for a single image"
)
async def verify_single_image(
    image_url: str = Query(..., description="URL of the image to verify"),
    green_threshold: float = Query(0.3, ge=0.0, le=1.0, description="Threshold for green verification"),
    current_user: dict = Depends(get_current_user),
):
    """
    Verify green coverage and detect cups for a single image URL.
    
    Returns verification result including:
    - Green verification stats.
    - List of detected cups with normalized coordinates [0.0 - 1.0].
    """
    # Bạn cần đảm bảo Service có hàm verify_single_image nhận logic tương tự verify_images
    return await GreenVerificationService.verify_single_image(image_url, green_threshold)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check green verification & cup detection service health"
)
async def health_check():
    """
    Check if the AI service orchestrator is ready.
    
    Returns status of:
    - Segmentation Model
    - Depth Model
    - Cup Detection Model
    """
    try:
        orchestrator = GreenVerificationService.get_orchestrator()
        
        # Kiểm tra xem Cup Detector đã được init chưa
        cup_status = "loaded" if orchestrator.cup_detector else "disabled/error"
        
        return {
            "status": "healthy",
            "segmentation_model": "loaded",
            "depth_model": "loaded",
            "cup_model": cup_status,
            "device": str(orchestrator.device)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }