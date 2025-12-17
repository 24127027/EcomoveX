from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.destination import GreenVerifiedStatus
from schemas.map_schema import PlaceDataCategory, PlaceDetailsRequest
from services.map_service import MapService
from utils.green_verification.orchestrator import GreenCoverageOrchestrator
from schemas.green_verification_schema import GreenVerificationResponse


class GreenVerificationService:
    '''
    DATA FLOW
    - use place_id to get place details
    - Get associated image URLs
    - For each image URL:
        - Run segmentation model to get green mask
        - Run depth model to get depth map
        - Calculate green coverage metrics
        - Run cup detection model to find cups
    - Return results with green scores and status
    
    Input: place_id
    Output: {
        score: float,
        tag: GreenVerifiedStatus
        }
    '''

    @classmethod
    async def verify_place_green_coverage(cls, place_id: str, db: AsyncSession, user_id: int) -> GreenVerificationResponse:
        """
        Verify green coverage for images associated with a place.

        Args:
            place_id: place_id của địa điểm
            db: Database session
            user_id: User ID for authentication

        Returns:
            GreenVerificationResponse with green_score and status
        """

        # 1. Fetch place info
        request = PlaceDetailsRequest(
            place_id=place_id,
            categories=[PlaceDataCategory.BASIC]
        )

        place_details = await MapService.get_location_details(request, db, user_id)

        # 2. Collect image URLs
        image_urls = [p.photo_url for p in (place_details.photos or []) if p.photo_url]

        # No images → Not Verified, score = 0
        if not image_urls:
            return GreenVerificationResponse(
                green_score=0.0,
                status=GreenVerifiedStatus.Not_Green_Verified
            )

        # 3. Process images with error handling for ML library compatibility issues
        try:
            orchestrator = GreenCoverageOrchestrator.get_instance()

            scores = []
            for url in image_urls:
                res = orchestrator.process_single_image(url)
                scores.append(res["green_score"])

            # 4. Aggregate score (mean)
            final_score = sum(scores) / len(scores)

            # 5. Determine status
            if final_score >= 0.02:
                verification_status = GreenVerifiedStatus.AI_Green_Verified
            else:
                verification_status = GreenVerifiedStatus.Not_Green_Verified

            # 6. Return final schema
            return GreenVerificationResponse(
                green_score=final_score,
                status=verification_status
            )

        except Exception as e:
            # Log the error
            print(f"[GreenVerification] ML processing failed: {e}")
            import traceback
            traceback.print_exc()

            # Return a fallback response indicating processing is unavailable
            # This allows the API to still work even if ML models fail to load
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Green verification service is currently unavailable due to ML model compatibility issues. Please contact administrator. Error: {str(e)[:100]}"
            )
