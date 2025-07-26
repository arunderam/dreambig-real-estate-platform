from typing import Tuple, Optional
import requests
from app.config import settings

def get_coordinates(address: str) -> Optional[Tuple[float, float]]:
    """Get latitude and longitude for an address using geocoding service"""
    # Mock implementation - in production use Google Maps API or similar
    # Example with Google Maps:
    # params = {
    #     "address": address,
    #     "key": settings.GOOGLE_MAPS_API_KEY
    # }
    # response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=params)
    # data = response.json()
    # if data["status"] == "OK":
    #     location = data["results"][0]["geometry"]["location"]
    #     return (location["lat"], location["lng"])
    return (12.9716, 77.5946)  # Default to Bangalore coordinates for demo

def calculate_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float
) -> float:
    """Calculate distance between two coordinates in kilometers"""
    # Using Haversine formula
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c