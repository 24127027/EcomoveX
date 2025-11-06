from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class ClusterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    algorithm: str = Field(..., min_length=1, max_length=100)

    @field_validator('name', 'algorithm')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()

class ClusterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    algorithm: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator('name', 'algorithm')
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip() if v else None

class UserClusterAssociationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    cluster_id: int = Field(..., gt=0)

class UserClusterBatchCreate(BaseModel):
    cluster_id: int = Field(..., gt=0)
    user_ids: List[int] = Field(..., min_length=1)

    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v: List[int]) -> List[int]:
        if any(uid <= 0 for uid in v):
            raise ValueError("All user IDs must be positive integers")
        return list(dict.fromkeys(v))

class ClusterDestinationCreate(BaseModel):
    cluster_id: int = Field(..., gt=0)
    destination_id: int = Field(..., gt=0)
    popularity_score: Optional[float] = Field(None, ge=0.0, le=100.0)

class ClusterDestinationUpdate(BaseModel):
    popularity_score: float = Field(..., ge=0.0, le=100.0)

class ClusterDestinationBatchCreate(BaseModel):
    cluster_id: int = Field(..., gt=0)
    destinations: List[dict] = Field(..., min_length=1)

    @field_validator('destinations')
    @classmethod
    def validate_destinations(cls, v: List[dict]) -> List[dict]:
        for dest in v:
            if 'destination_id' not in dest:
                raise ValueError("Each destination must have a 'destination_id'")
            if not isinstance(dest['destination_id'], int) or dest['destination_id'] <= 0:
                raise ValueError("All destination IDs must be positive integers")
            if 'popularity_score' in dest:
                score = dest['popularity_score']
                if score is not None and (not isinstance(score, (int, float)) or score < 0 or score > 100):
                    raise ValueError("Popularity scores must be between 0 and 100")
        return v
