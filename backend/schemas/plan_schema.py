from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from models.plan import DestinationType, PlanRole


# --- INPUT SCHEMAS ---
class PlanDestinationCreate(BaseModel):
    id: int = 0  # Thêm default 0 để frontend gửi 0 không bị lỗi
    destination_id: str
    destination_type: DestinationType
    order_in_day: int
    visit_date: datetime
    time: Optional[str] = None  # ✅ Thêm time_slot (format: "HH:MM")
    estimated_cost: Optional[float] = Field(0, ge=0)
    url: Optional[str] = None
    note: Optional[str] = None

    @field_validator("visit_date")
    @classmethod
    def remove_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


class PlanDestinationUpdate(BaseModel):
    visit_date: Optional[datetime] = None
    order_in_day: Optional[int] = None
    time: Optional[str] = None  # ✅ Thêm time_slot
    estimated_cost: Optional[float] = Field(None, ge=0)
    url: Optional[str] = None
    note: Optional[str] = None

    @field_validator("visit_date")
    @classmethod
    def remove_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


class PlanMemberCreate(BaseModel):
    user_id: int
    role: PlanRole = PlanRole.member


# --- RESPONSE SCHEMAS ---
class PlanDestinationResponse(BaseModel):
    id: int
    destination_id: str
    destination_type: DestinationType
    type: DestinationType
    order_in_day: int
    visit_date: datetime
    time: Optional[str] = None  # ✅ Thêm time_slot
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


# --- PLAN MAIN SCHEMAS ---
class PlanCreate(BaseModel):
    place_name: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    budget_limit: Optional[float] = Field(None, gt=0)
    # [FIX] Dùng PlanDestinationCreate thay vì Response
    destinations: List[PlanDestinationCreate] = Field(default_factory=list)

    @field_validator("place_name")
    @classmethod
    def validate_place_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Place name cannot be empty")
        return v.strip()


class PlanUpdate(BaseModel):
    place_name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_limit: Optional[float] = Field(None, gt=0)
    # [FIX] Dùng PlanDestinationCreate
    destinations: Optional[List[PlanDestinationCreate]] = Field(default_factory=list)


class PlanResponse(BaseModel):
    id: int
    place_name: str
    start_date: date
    end_date: date
    budget_limit: Optional[float] = None
    destinations: List[PlanDestinationResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


# --- MEMBER & OTHER ---
class MemberCreate(BaseModel):
    ids: List[int] = Field(..., min_length=1)


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
