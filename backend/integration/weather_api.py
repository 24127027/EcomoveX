from typing import Optional
from utils.config import settings
from schemas.weather_schema import *
import json
import httpx

class WeatherAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        self.base_url = "https://weather.googleapis.com/v1"
        self.current_weather_endpoint = "/currentConditions:lookup"
        self.forecast_endpoint = "/forecast/hours:lookup"

        self.client = httpx.AsyncClient()
    
    async def get_current(self, 
                      param: CurrentWeatherRequest
                      ) -> CurrentWeatherResponse:
        
        params = {
            "location.latitude": param.location.latitude,
            "location.longitude": param.location.longitude,
            "key": self.api_key,
            "unitsSystem": param.unit_system
        }
        url = f"{self.base_url}{self.current_weather_endpoint}"

        response = await self.client.get(
            url,
            params=params
        )
        
        if response.status_code != 200:
            raise ValueError(f"Error fetching current weather: HTTP {response.status_code}")
        
        data = response.json()
        if "error" in data:
            raise ValueError(f"Error in current weather response: {data.get('error')}")
        
        weatherCondition = data.get("weatherCondition")
        temperature = data.get("temperature", {}).get("degrees")
        feelslike_temperature = data.get("feelsLikeTemperature", {}).get("degrees")
        humidity = data.get("relativeHumidity")
        cloud_cover = data.get("cloudCover")
        history = data.get("currentConditionsHistory", {})

        return CurrentWeatherResponse(
            temperature=Temperature(
                temperature=temperature,
                feelslike_temperature=feelslike_temperature,
                min_temperature=history.get("minTemperature", {}).get("degrees"),
                max_temperature=history.get("maxTemperature", {}).get("degrees")
            ),
            weather_condition=WeatherCondition(
                description=weatherCondition.get("description", {}).get("text"),
                icon_base_uri=weatherCondition.get("iconBaseUri"),
                type=weatherCondition.get("type")
            ),
            humidity=humidity,
            cloud_cover=cloud_cover,
            is_daytime=data.get("isDaytime")
        )
    
    async def get_forecast_hourly(self,
                              param: ForecastRequest
                              ) -> WeatherForecastResponse:
        params = {
            "location.latitude": param.location.latitude,
            "location.longitude": param.location.longitude,
            "key": self.api_key,
            "unitsSystem": param.unit_system,
            "hours": param.hours
        }

        url = f"{self.base_url}{self.forecast_endpoint}"
        response = await self.client.get(
            url,
            params=params
        )

        if response.status_code != 200:
            raise ValueError(f"Error fetching forecast: HTTP {response.status_code}")
        
        data = response.json()
        if "error" in data:
            raise ValueError(f"Error in forecast response: {data.get('error')}")
        
        hourly_data = []
        for hour in data.get("forecastHours", []):
            weatherCondition = hour.get("weatherCondition")
            temperature = hour.get("temperature", {}).get("degrees")
            feelslike_temperature = hour.get("feelsLikeTemperature", {}).get("degrees")
            humidity = hour.get("relativeHumidity")
            cloud_cover = hour.get("cloudCover")
            is_daytime = hour.get("isDaytime")
            interval = hour.get("interval")
            display_date_time = hour.get("displayDateTime")

            hourly_data.append(
                HourlyDataPoint(
                    interval=Interval(**interval),
                    display_date_time=DisplayDateTime(**display_date_time),
                    temperature=Temperature(
                        temperature=temperature,
                        feelslike_temperature=feelslike_temperature
                    ),
                    weather_condition=WeatherCondition(
                        description=weatherCondition.get("description", {}).get("text"),
                        icon_base_uri=weatherCondition.get("iconBaseUri"),
                        type=weatherCondition.get("type")
                    ),
                    humidity=humidity,
                    cloud_cover=cloud_cover,
                    is_daytime=is_daytime
                )
            )

        return WeatherForecastResponse(
            hourly_forecast=hourly_data
        )

    async def close(self):
        await self.client.aclose()
    
async def create_weather_client(api_key: Optional[str] = None) -> WeatherAPI:
    return WeatherAPI(api_key=api_key)