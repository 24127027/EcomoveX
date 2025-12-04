from typing import List, Optional
from pydantic import BaseModel, HttpUrl

# --- THÊM CLASS MỚI CHO CUP ---
class CupDetectionResult(BaseModel):
    label: str
    confidence: float
    normalized_point: List[float]  # [x, y] ví dụ: [0.45, 0.67]
    # Có thể thêm bbox nếu muốn, nhưng bạn ưu tiên normalized_point
    # normalized_bbox: Optional[List[float]] = None 

# --- CẬP NHẬT CLASS KẾT QUẢ ---
class ImageVerificationResult(BaseModel):
    url: str
    green_score: float
    green_proportion: float
    depth_weighted_score: float
    verified: bool
    # Thêm trường này vào
    cup_detections: List[CupDetectionResult] = [] 
    error: Optional[str] = None

class GreenVerificationRequest(BaseModel):
    image_urls: List[str]
    green_threshold: float = 0.3

class GreenVerificationResponse(BaseModel):
    results: List[ImageVerificationResult]
    summary: dict