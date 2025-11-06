from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Tuple
from datetime import date
from models.plan import DestinationType

class PlanRequestCreate(BaseModel):
    place_name: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    budget_limit: Optional[float] = Field(None, gt=0)

    @field_validator('place_name')
    @classmethod
    def validate_place_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Place name cannot be empty or whitespace")
        return v.strip()

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError("End date must be after or equal to start date")
        return v

class PlanRequestUpdate(BaseModel):
    place_name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_limit: Optional[float] = Field(None, gt=0)

    @field_validator('place_name')
    @classmethod
    def validate_place_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Place name cannot be empty or whitespace")
        return v.strip() if v else None

class DestinationInfo(BaseModel):
    longitude: float
    latitude: float
    visit_date: date
    type: DestinationType

class PlanResponse(BaseModel):
    id: int
    user_id: int
    place_name: str
    start_date: date
    end_date: date
    budget_limit: Optional[float] = None
    destinations: List[DestinationInfo]

    model_config = ConfigDict(from_attributes=True)