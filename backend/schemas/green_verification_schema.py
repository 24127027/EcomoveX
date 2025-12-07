from typing import List, Literal
from pydantic import BaseModel, HttpUrl
from destination_schema import GreenVerifiedStatus
class GreenVerificationResponse(BaseModel):
    green_score: float
    status: GreenVerifiedStatus