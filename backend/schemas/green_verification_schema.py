from pydantic import BaseModel
from .destination_schema import GreenVerifiedStatus
class GreenVerificationResponse(BaseModel):
    green_score: float
    status: GreenVerifiedStatus
