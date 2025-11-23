from schemas.destination_schema import Location
from integration.weather_api import create_weather_client
from schemas.weather_schema import CurrentWeatherResponse, WeatherForecastResponse, CurrentWeatherRequest, ForecastRequest
from fastapi import HTTPException, status
from typing import Tuple

class WeatherService:
    @staticmethod
    async def get_current_weather(location: Location, unit_system: str = "METRIC") -> CurrentWeatherResponse:
        try:
            try:
                weather_client = await create_weather_client()
                param = CurrentWeatherRequest(location=location, unit_system=unit_system)
                return await weather_client.get_current(param=param)
            finally:
                if weather_client:
                    await weather_client.close()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get current weather data: {str(e)}"
            )

    @staticmethod
    async def get_hourly_forecast(location: Location, hours: int = 24, unit_system: str = "METRIC") -> WeatherForecastResponse:
        try:
            try:
                weather_client = await create_weather_client()
                param = ForecastRequest(location=location, hours=hours, unit_system=unit_system)
                return await weather_client.get_forecast_hourly(param=param)
            finally:
                if weather_client:
                    await weather_client.close()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get hourly forecast data: {str(e)}"
            )