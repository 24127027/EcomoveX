from schemas.destination_schema import Location
from integration.weather_api import create_weather_client
from schemas.weather_schema import CurrentWeatherResponse, WeatherForecastResponse, CurrentWeatherRequest, ForecastRequest
from schemas.map_schema import PlaceDetailsRequest, PlaceDataCategory
from fastapi import HTTPException, status
from services.map_service import MapService

class WeatherService:
    @staticmethod
    async def get_current_weather(place_id: str, unit_system: str = "METRIC") -> CurrentWeatherResponse:
        weather_client = None
        try:
            request_data = PlaceDetailsRequest(
                place_id=place_id,
                categories=[PlaceDataCategory.BASIC]
            )
            detail = await MapService.get_location_details(request_data)
            location = detail.geometry.location
            weather_client = await create_weather_client()
            param = CurrentWeatherRequest(location=location, unit_system=unit_system)
            return await weather_client.get_current(param=param)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get current weather data: {str(e)}"
            )
        finally:
            if weather_client:
                await weather_client.close()

    @staticmethod
    async def get_hourly_forecast(place_id: str, hours: int = 24, unit_system: str = "METRIC") -> WeatherForecastResponse:
        weather_client = None
        try:
            request_data = PlaceDetailsRequest(
                place_id=place_id,
                categories=[PlaceDataCategory.BASIC]
            )
            detail = await MapService.get_location_details(request_data)
            location = detail.geometry.location
            weather_client = await create_weather_client()
            param = ForecastRequest(location=location, hours=hours, unit_system=unit_system)
            return await weather_client.get_forecast_hourly(param=param)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get hourly forecast data: {str(e)}"
            )
        finally:
            if weather_client:
                await weather_client.close()