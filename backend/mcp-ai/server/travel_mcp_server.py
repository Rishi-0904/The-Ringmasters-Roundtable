# backend/mcp-ai/server/travel_mcp_server.py
import os
import sys
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Ensure the parent directory is in search path to import existing agent files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from map_agent import MapAgent
from weather_agent import WeatherAgent
from event_agent import EventAgent
from itinerary_agent import ItineraryAgent
from budget_agent import BudgetAgent

# Initialize FastMCP Server
mcp = FastMCP("Roundtable Travel Assistant Server")

# Instantiate Shared Logic
map_core = MapAgent()
event_core = EventAgent()
itinerary_core = ItineraryAgent()
budget_core = BudgetAgent()

# API Keys loaded from environments
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "144f40803196f5205a5d86fa652a4720")
weather_core = WeatherAgent(OPENWEATHER_API_KEY)


@mcp.tool()
def calculate_route(start_city: str, end_city: str, num_days: Optional[int] = 10) -> List[Dict[str, Any]]:
    """
    Calculates travel routing coordinates and lists major intermediate cities.
    Reuses business logic from MapAgent.
    """
    try:
        return map_core.get_intermediate_cities(
            start_city=start_city,
            end_city=end_city,
            num_days=num_days
        )
    except Exception as e:
        return [{"error": f"Failed to calculate route: {str(e)}", "city": start_city, "coord": "0,0"}]


@mcp.tool()
def get_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Retrieves weather forecast (description and temperature in Celsius) for specific lat/lon.
    Reuses business logic from WeatherAgent.
    """
    try:
        return weather_core.get_weather(lat=lat, lon=lon)
    except Exception as e:
        return {"weather": "Forecast unavailable", "temp": 0.0, "error": str(e)}


@mcp.tool()
def find_events(city: str) -> List[Dict[str, Any]]:
    """
    Finds upcoming cultural events and tourist attractions in a city.
    Reuses business logic from EventAgent.
    """
    try:
        return event_core.get_events(city=city)
    except Exception as e:
        return event_core.get_fallback_events(city=city)


@mcp.tool()
def generate_itinerary(route_with_weather: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates a structured, chronological daily activity itinerary plan.
    Each item in route_with_weather must contain:
    { "city": "CityName", "weather": { "weather": "Cloudy", "temp": 24.0 } }
    Reuses business logic from ItineraryAgent.
    """
    try:
        return itinerary_core.generate_itinerary(route_data=route_with_weather)
    except Exception as e:
        return [{"day": 1, "city": "Travel Route", "activities": [{"title": "Explore city center", "type": "sightseeing"}]}]


@mcp.tool()
def compute_budget(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    adults: Optional[int] = 1,
    num_days: Optional[int] = 1,
    transport_mode: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes a comprehensive budget summary including flight, train, and lodging pricing.
    transport_mode can be 'flight', 'train', or 'road_trip' to filter results.
    Reuses business logic from BudgetAgent.
    """
    payload = {
        "start_city": origin,
        "end_city": destination,
        "start_date": start_date,
        "end_date": end_date,
        "adults": adults,
        "num_days": num_days,
        "transport_mode": transport_mode
    }
    try:
        return budget_core.generate_budget_summary(payload)
    except Exception as e:
        return {
            "source": "budget_agent",
            "error": str(e),
            "notes": ["Resilience fallback engaged. Cost estimations could not be calculated."]
        }


if __name__ == "__main__":
    mcp.run()
