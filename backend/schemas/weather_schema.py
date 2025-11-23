from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from schemas.destination_schema import Location

class Temperature(BaseModel):
    temperature: float  # in Celsius
    feelslike_temperature: float  # in Celsius
    max_temperature: Optional[float] = None
    min_temperature: Optional[float] = None

class WeatherCondition(BaseModel):
    description: str
    icon_base_uri: str
    type: str  # e.g., "CLEAR", "CLOUDY", "RAINY"

class Interval(BaseModel):
    """Represents a UTC time interval."""
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")

class DisplayDateTime(BaseModel):
    """Represents the components of a local date and time."""
    year: int
    month: int
    day: int
    hours: int
    utc_offset: str = Field(..., alias="utcOffset", example="-28800s")

class CurrentWeatherRequest(BaseModel):
    location: Location  # Location object with latitude and longitude
    unit_system: Optional[str] = "METRIC"  # "METRIC" or "IMPERIAL"
    
class ForecastRequest(BaseModel):
    location: Location  # Location object with latitude and longitude
    hours: int  
    unit_system: Optional[str] = "METRIC"  # "METRIC" or "IMPERIAL"

class HourlyDataPoint(BaseModel):
    interval: Interval
    display_date_time: DisplayDateTime
    temperature: Temperature
    weather_condition: WeatherCondition
    humidity: float
    cloud_cover: float
    is_daytime: bool

class WeatherForecastResponse(BaseModel):
    hourly_forecast: List[HourlyDataPoint]

    model_config = ConfigDict(from_attributes=True)

class CurrentWeatherResponse(BaseModel):
    temperature: Temperature
    weather_condition: WeatherCondition
    humidity: float  # in percentage
    cloud_cover: float  # in percentage
    is_daytime: bool

    model_config = ConfigDict(from_attributes=True)