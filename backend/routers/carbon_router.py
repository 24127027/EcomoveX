from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from database.user_database import get_user_db
from schemas.carbon_schema import CarbonEmissionCreate, CarbonEmissionResponse, CarbonEmissionUpdate
from services.carbon_service import CarbonService
from utils.authentication_util import get_current_user
from typing import List
from datetime import datetime

router = APIRouter(prefix="/carbon", tags=["Carbon Emissions"])

@router.post("/calculate", response_model=CarbonEmissionResponse, status_code=status.HTTP_201_CREATED)
async def calculate_carbon_emission(
    request: CarbonEmissionCreate,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    new_emission = await CarbonService.create_carbon_emission(
        db=db,
        user_id=current_user["user_id"],
        create_data=request
    )
    
    return new_emission

@router.get("/me", response_model=List[CarbonEmissionResponse])
async def get_my_carbon_emissions(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.get_user_carbon_emissions(db, current_user["user_id"])

@router.get("/me/total")
async def get_my_total_carbon(
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.get_total_carbon_by_user(db, current_user["user_id"])

@router.get("/me/total/day")
async def get_my_total_carbon_by_day(
    date: datetime,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.get_total_carbon_by_day(db, current_user["user_id"], date)

@router.get("/me/total/week")
async def get_my_total_carbon_by_week(
    date: datetime,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.get_total_carbon_by_week(db, current_user["user_id"], date)

@router.get("/me/total/month")
async def get_my_total_carbon_by_month(
    date: datetime,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.get_total_carbon_by_month(db, current_user["user_id"], date)

@router.get("/me/total/year")
async def get_my_total_carbon_by_year(
    year: int = Query(..., ge=2000, le=2100, description="Year (2000-2100)"),
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.get_total_carbon_by_year(db, current_user["user_id"], year)

@router.get("/me/total/range")
async def get_my_total_carbon_by_range(
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.get_total_carbon_by_date_range(db, current_user["user_id"], start_date, end_date)

@router.get("/{emission_id}", response_model=CarbonEmissionResponse)
async def get_carbon_emission_by_id(
    emission_id: int = Path(..., gt=0, description="Carbon emission ID"),
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.get_carbon_emission_by_id(db, emission_id, current_user["user_id"])

@router.put("/{emission_id}", response_model=CarbonEmissionResponse)
async def update_carbon_emission(
    emission_id: int = Path(..., gt=0, description="Carbon emission ID"),
    updated_data: CarbonEmissionUpdate = ...,
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.update_carbon_emission(db, emission_id, current_user["user_id"], updated_data)

@router.delete("/{emission_id}")
async def delete_carbon_emission(
    emission_id: int = Path(..., gt=0, description="Carbon emission ID"),
    db: AsyncSession = Depends(get_user_db),
    current_user: dict = Depends(get_current_user)
):
    return await CarbonService.delete_carbon_emission(db, emission_id, current_user["user_id"])
