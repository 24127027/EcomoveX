from fastapi import HTTPException, status

from utils.green_verification.greenness.orchestrator import GreenCoverageOrchestrator
from schemas.green_verification_schema import (
    GreenVerificationRequest,
    GreenVerificationResponse,
    ImageVerificationResult,
)


class GreenVerificationService:
    """Service for green coverage verification using segmentation and depth analysis."""

    _orchestrator = None

    @classmethod
    def get_orchestrator(cls) -> GreenCoverageOrchestrator:
        """Get or create singleton orchestrator instance."""
        if cls._orchestrator is None:
            try:
                cls._orchestrator = GreenCoverageOrchestrator(
                    segmentation_model="best.pt",
                    depth_model_type="midas_v21_small_256",
                    depth_model_path=None,
                    green_threshold=0.3,  # default, can be overridden per request
                    optimize=True,
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize green verification orchestrator: {str(e)}"
                )
        return cls._orchestrator

    @staticmethod
    async def verify_images(
        request: GreenVerificationRequest,
    ) -> GreenVerificationResponse:
        """
        Verify green coverage for a list of image URLs.

        Args:
            request: Contains image URLs and optional threshold

        Returns:
            GreenVerificationResponse with results and summary
        """
        try:
            # Get orchestrator
            orchestrator = GreenVerificationService.get_orchestrator()

            # Override threshold if provided
            original_threshold = orchestrator.green_threshold
            if request.green_threshold is not None:
                orchestrator.green_threshold = request.green_threshold

            # Process images
            raw_results = orchestrator.process_image_list(request.image_urls)

            # Convert to response format
            results = [
                ImageVerificationResult(
                    url=r["url"],
                    green_proportion=r["green_proportion"],
                    depth_weighted=r["depth_weighted"],
                    green_score=r["green_score"],
                    verified=r["verified"],
                    error=r.get("error"),
                )
                for r in raw_results
            ]

            # Get summary statistics
            summary = orchestrator.get_summary_stats(raw_results)

            # Restore original threshold
            orchestrator.green_threshold = original_threshold

            return GreenVerificationResponse(results=results, summary=summary)

        except RuntimeError as re:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Green verification service unavailable: {str(re)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying images: {str(e)}",
            )

    @staticmethod
    async def verify_single_image(
        image_url: str, green_threshold: float = 0.3
    ) -> ImageVerificationResult:
        """
        Verify green coverage for a single image URL.

        Args:
            image_url: URL of the image to verify
            green_threshold: Threshold for verification (0-1)

        Returns:
            ImageVerificationResult
        """
        try:
            orchestrator = GreenVerificationService.get_orchestrator()

            # Override threshold
            original_threshold = orchestrator.green_threshold
            orchestrator.green_threshold = green_threshold

            # Process single image
            result = orchestrator.process_single_image(image_url)

            # Restore threshold
            orchestrator.green_threshold = original_threshold

            return ImageVerificationResult(
                url=result["url"],
                green_proportion=result["green_proportion"],
                depth_weighted=result["depth_weighted"],
                green_score=result["green_score"],
                verified=result["verified"],
                error=result.get("error"),
            )

        except RuntimeError as re:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Green verification service unavailable: {str(re)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying image: {str(e)}",
            )
