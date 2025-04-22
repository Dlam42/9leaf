# test_geopy.py
from geopy.geocoders import Nominatim
try:
    geolocator = Nominatim(user_agent="my_test_app_123") # Use a unique agent for testing
    location = geolocator.geocode("1600 Amphitheatre Parkway, Mountain View, CA")
    if location:
        print(f"Success: {location.address}")
        print(f"Coords: {location.latitude}, {location.longitude}")
    else:
        print("Failed: No location found.")
except Exception as e:
    print(f"Error: {e}")