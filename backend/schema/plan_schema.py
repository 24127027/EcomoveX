from pydantic import BaseModel
from typing import Optional, List, Tuple
from datetime import date
from models.plan import DestinationType

class PlanRequestCreate(BaseModel):
    place_name: str
    start_date: date
    end_date: date
    budget_limit: Optional[float] = None

class PlanRequestUpdate(BaseModel):
    place_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_limit: Optional[float] = None

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

    model_config = {
        "from_attributes": True
    }