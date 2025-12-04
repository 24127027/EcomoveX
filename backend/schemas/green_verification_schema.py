from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class GreenVerificationRequest(BaseModel):
    """Request model for green verification of image URLs."""
    image_urls: List[str] = Field(..., min_length=1, max_length=20, description="List of image URLs to verify")
    green_threshold: Optional[float] = Field(0.3, ge=0.0, le=1.0, description="Threshold for green verification")


class ImageVerificationResult(BaseModel):
    """Result for a single image verification."""
    url: str
    green_proportion: float = Field(..., description="Proportion of green pixels (0-1)")
    depth_weighted: float = Field(..., description="Depth-weighted green score (0-1)")
    green_score: float = Field(..., description="Final green score (proportion * depth_weighted)")
    verified: bool = Field(..., description="Whether the image meets green threshold")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class GreenVerificationResponse(BaseModel):
    """Response model for green verification."""
    results: List[ImageVerificationResult]
    summary: Dict[str, Any] = Field(..., description="Summary statistics")


class GreenVerificationSummary(BaseModel):
    """Summary statistics for green verification batch."""
    total_images: int
    valid_images: int
    verified_images: int
    average_green_proportion: float
    average_green_score: float
    verification_rate: float