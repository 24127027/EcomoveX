from fastapi import HTTPException, status

from backend.models.destination import GreenVerifiedStatus
from backend.schemas.map_schema import PlaceDataCategory, PlaceDetailsRequest, PlaceDetailsResponse
from backend.services.map_service import MapService
from backend.utils.green_verification.orchestrator import GreenCoverageOrchestrator
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
    async def verify_place_green_coverage(cls, place_id: str) -> List[Dict[str, Any]]:
        """
        Verify green coverage for images associated with a place.

        Args:
            place_id: place_id của địa điểm

        Returns:
            List[{ url, green_score, verified }]
        """

        # 1. Fetch place info
        request = PlaceDetailsRequest(
            place_id=place_id,
            categories=[PlaceDataCategory.BASIC]
        )

        place_details = await MapService.get_location_details(request)

        # 2. Collect image URLs
        image_urls = [p.photo_url for p in (place_details.photos or []) if p.photo_url]

        # No images → Not Verified, score = 0
        if not image_urls:
            return GreenVerificationResponse(
                green_score=0.0,
                status=GreenVerifiedStatus.Not_Green_Verified
            )

        # 3. Process images directly (bỏ GreenVerificationRequest)
        orchestrator = GreenCoverageOrchestrator.get_instance()

        scores = []
        for url in image_urls:
            res = orchestrator.process_single_image(url)
            scores.append(res["green_score"])

        # 4. Aggregate score (mean)
        final_score = sum(scores) / len(scores)

        # 5. Determine status
        if final_score >= 0.02:
            status = GreenVerifiedStatus.AI_Green_Verified
        else:
            status = GreenVerifiedStatus.Not_Green_Verified

        # 6. Return final schema
        return GreenVerificationResponse(
            green_score=final_score,
            status=status
        )
