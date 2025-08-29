"""Weather tool for getting weather information."""

import aiohttp
import json
from typing import List, Optional

from ..base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from ....utils.logger import get_logger

logger = get_logger("weather_tool")


class WeatherTool(BaseTool):
    """Tool for getting weather information."""
    
    def __init__(self):
        super().__init__()
        # Using a free weather API (OpenWeatherMap requires API key)
        # For demo purposes, we'll use a mock implementation
        # In production, you should use a real weather API
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        
    def get_name(self) -> str:
        return "weather"
        
    def get_description(self) -> str:
        return "Get current weather information for a specified location."
        
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="location",
                type=ToolParameterType.STRING,
                description="City name or location (e.g., 'Beijing', 'New York', 'London')",
                required=True
            ),
            ToolParameter(
                name="units",
                type=ToolParameterType.STRING,
                description="Temperature units",
                required=False,
                default="metric",
                enum=["metric", "imperial", "kelvin"]
            )
        ]
        
    async def _get_weather_data(self, location: str, units: str) -> dict:
        """Get weather data from API."""
        # For demo purposes, return mock data
        # In production, implement real API call
        mock_data = {
            "beijing": {
                "temperature": 15,
                "description": "Partly cloudy",
                "humidity": 65,
                "wind_speed": 12,
                "pressure": 1013
            },
            "shanghai": {
                "temperature": 18,
                "description": "Clear sky",
                "humidity": 58,
                "wind_speed": 8,
                "pressure": 1015
            },
            "new york": {
                "temperature": 22,
                "description": "Sunny",
                "humidity": 45,
                "wind_speed": 15,
                "pressure": 1018
            },
            "london": {
                "temperature": 12,
                "description": "Light rain",
                "humidity": 78,
                "wind_speed": 18,
                "pressure": 1008
            }
        }
        
        location_key = location.lower()
        if location_key in mock_data:
            data = mock_data[location_key].copy()
            
            # Convert temperature based on units
            temp_celsius = data["temperature"]
            if units == "imperial":
                data["temperature"] = round(temp_celsius * 9/5 + 32, 1)
                data["temp_unit"] = "°F"
            elif units == "kelvin":
                data["temperature"] = round(temp_celsius + 273.15, 1)
                data["temp_unit"] = "K"
            else:
                data["temp_unit"] = "°C"
                
            return data
        else:
            # Return a generic response for unknown locations
            return {
                "temperature": 20,
                "description": "Weather data not available for this location",
                "humidity": 50,
                "wind_speed": 10,
                "pressure": 1013,
                "temp_unit": "°C" if units == "metric" else ("°F" if units == "imperial" else "K")
            }
            
    async def execute(self, location: str, units: str = "metric") -> ToolResult:
        """Execute the weather tool."""
        try:
            logger.info(f"Getting weather for location: {location}, units: {units}")
            
            # Get weather data
            weather_data = await self._get_weather_data(location, units)
            
            # Format the result
            result = {
                "location": location.title(),
                "temperature": f"{weather_data['temperature']}{weather_data['temp_unit']}",
                "description": weather_data["description"],
                "humidity": f"{weather_data['humidity']}%",
                "wind_speed": f"{weather_data['wind_speed']} km/h",
                "pressure": f"{weather_data['pressure']} hPa"
            }
            
            # Create a human-readable summary
            summary = (
                f"Weather in {result['location']}: {result['temperature']}, "
                f"{result['description']}. Humidity: {result['humidity']}, "
                f"Wind: {result['wind_speed']}, Pressure: {result['pressure']}"
            )
            
            logger.info(f"Weather query successful for {location}")
            
            return ToolResult(
                success=True,
                result={
                    "summary": summary,
                    "details": result
                },
                metadata={
                    "location": location,
                    "units": units,
                    "data_source": "mock_api"  # In production, use real API source
                }
            )
            
        except Exception as e:
            logger.error(f"Weather tool error: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                result=None,
                error=f"Failed to get weather information: {str(e)}"
            )