from fastapi import APIRouter, Query, status
from schemas.weather_schema import CurrentWeatherResponse, WeatherForecastResponse
from schemas.destination_schema import Location
from services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/current", response_model=CurrentWeatherResponse, status_code=status.HTTP_200_OK)
async def get_current_weather(
    place_id: str = Query(..., description="Place ID to get location details"),
    unit_system: str = Query("METRIC", description="Unit system: METRIC or IMPERIAL")
):
    """Get current weather conditions for a specific location."""
    result = await WeatherService.get_current_weather(place_id=place_id, unit_system=unit_system)
    return result

@router.get("/forecast", response_model=WeatherForecastResponse, status_code=status.HTTP_200_OK)
async def get_hourly_forecast(
    place_id: str = Query(..., description="Place ID to get location details"),
    hours: int = Query(24, ge=1, le=120, description="Number of hours to forecast"),
    unit_system: str = Query("METRIC", description="Unit system: METRIC or IMPERIAL")
):
    """Get hourly weather forecast for a specific location."""
    result = await WeatherService.get_hourly_forecast(place_id=place_id, hours=hours, unit_system=unit_system)
    return result