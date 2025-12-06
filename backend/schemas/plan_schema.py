from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.plan import DestinationType, PlanRole, TimeSlot
from schemas.route_schema import RouteForPlanResponse


class PlanDestinationCreate(BaseModel):
    destination_id: str
    destination_type: DestinationType
    order_in_day: int
    visit_date: date
    estimated_cost: Optional[float] = Field(None, ge=0)
    url: Optional[str] = None
    note: Optional[str] = None
    time_slot: TimeSlot


class PlanMemberCreate(BaseModel):
    user_id: int
    role: PlanRole = PlanRole.member


class PlanDestinationUpdate(BaseModel):
    visit_date: Optional[date] = None
    order_in_day: Optional[int] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    url: Optional[str] = None
    note: Optional[str] = None
    time_slot: Optional[TimeSlot] = None


class PlanDestinationResponse(BaseModel):
    id: int
    destination_id: str
    type: DestinationType
    order_in_day: int
    visit_date: date
    estimated_cost: Optional[float] = None
    url: Optional[str] = None
    note: Optional[str] = None
    time_slot: TimeSlot

    model_config = ConfigDict(from_attributes=True)


class PlanCreate(BaseModel):
    place_name: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    budget_limit: Optional[float] = Field(None, gt=0)
    destinations: List[PlanDestinationCreate] = Field(default_factory=list)  

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
    destinations: Optional[List[PlanDestinationCreate]] = Field(default_factory=list)  # ✅ Sửa: dùng PlanDestinationCreate

    @field_validator("place_name")
    @classmethod
    def validate_place_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Place name cannot be empty or whitespace")
        return v.strip() if v else None


class PlanResponse(BaseModel):
    id: int
    user_id: int  # ✅ Owner ID - REQUIRED for ownership checks
    place_name: str
    start_date: date
    end_date: date
    budget_limit: Optional[float] = None
    destinations: List[PlanDestinationResponse] = Field(default_factory=list)
    route: Optional[List[RouteForPlanResponse]] = None

    model_config = ConfigDict(from_attributes=True)
    

class PlanResponseBasic(BaseModel):
    id: int
    place_name: str
    budget_limit: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class AllPlansResponse(BaseModel):
    plans: List[PlanResponseBasic] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class MemberCreate(BaseModel):
    ids: List[PlanMemberCreate] = Field(..., min_length=1)


class MemberDelete(BaseModel):
    ids: List[int] = Field(..., min_length=1)


class PlanMemberDetailResponse(BaseModel):
    user_id: int
    plan_id: int
    role: PlanRole
    joined_at: datetime
    username: Optional[str] = None  # ✅ Add username for display
    email: Optional[str] = None     # ✅ Add email as fallback

    model_config = ConfigDict(from_attributes=True)


class PlanMemberResponse(BaseModel):
    plan_id: int
    members: List[PlanMemberDetailResponse] = Field(..., min_length=1)

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


class ActionResult(BaseModel):
    intent: str
    entities: Dict[str, Any]
    confidence: float
    plan_id: int = None
    action: str = None