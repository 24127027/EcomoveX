from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.plan import DestinationType, PlanRole


class PlanDestinationCreate(BaseModel):
    destination_id: str
    destination_type: DestinationType
    order_in_day: int
    visit_date: date
    estimated_cost: Optional[float] = Field(None, ge=0)
    url: Optional[str] = None
    note: Optional[str] = None
    
class PlanDestinationUpdate(BaseModel):
    visit_date: Optional[date] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    note: Optional[str] = None
    url: Optional[str] = None

class PlanMemberCreate(BaseModel):
    user_id: int
    role: PlanRole = PlanRole.member


class PlanDestinationUpdate(BaseModel):
    visit_date: Optional[date] = None
    order_in_day: Optional[int] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    url: Optional[str] = None
    note: Optional[str] = None


class PlanDestinationResponse(BaseModel):
    id: int
    destination_id: str
    type: DestinationType
    order_in_day: int
    visit_date: date
    estimated_cost: Optional[float] = None
    url: Optional[str] = None
    note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PlanMemberDetailResponse(BaseModel):
    user_id: int
    plan_id: int
    role: PlanRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanCreate(BaseModel):
    place_name: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    budget_limit: Optional[float] = Field(None, gt=0)
    destinations: List[PlanDestinationResponse] = Field(default_factory=list)

    @field_validator("place_name")
    @classmethod
    def validate_place_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Place name cannot be empty or whitespace")
        return v.strip()

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date, info) -> date:
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("End date must be after or equal to start date")
        return v


class PlanUpdate(BaseModel):
    place_name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_limit: Optional[float] = Field(None, gt=0)
    destinations: Optional[List[PlanDestinationResponse]] = Field(default_factory=list)

    @field_validator("place_name")
    @classmethod
    def validate_place_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Place name cannot be empty or whitespace")
        return v.strip() if v else None


class PlanResponse(BaseModel):
    id: int
    place_name: str
    start_date: date
    end_date: date
    budget_limit: Optional[float] = None
    destinations: List[PlanDestinationResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MemberCreate(BaseModel):
    ids: List[PlanMemberCreate] = Field(..., min_length=1)


class MemberDelete(BaseModel):
    ids: List[int] = Field(..., min_length=1)


class PlanMemberResponse(BaseModel):
    plan_id: int
    ids: List[int] = Field(..., min_length=1)

    model_config = ConfigDict(from_attributes=True)


class IntentHandlerResponse(BaseModel):
    ok: bool
    message: Optional[str] = None
    action: Optional[str] = None
    item: Optional[Dict[str, Any]] = None
    item_id: Optional[int] = None
    budget: Optional[float] = None
    plan: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[Any]] = None

    model_config = ConfigDict(from_attributes=True)
