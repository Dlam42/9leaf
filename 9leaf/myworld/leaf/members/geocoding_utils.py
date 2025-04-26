from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import re
import time

class GeocodingService:
    """A utility class for geocoding addresses with better error handling and formatting"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="leaf_geocoding_service", timeout=10)
    
    def format_address(self, address, city, state, zip_code=None):
        """Format address components into a standardized form for geocoding"""
        # Remove common apt/unit designators that can confuse geocoding
        clean_address = re.sub(r'\b(apt|unit|suite|ste|#)[.\s]*[a-zA-Z0-9-]+\b', '', address, flags=re.IGNORECASE)
        clean_address = clean_address.strip().rstrip(',')
        
        # Build address with comma separators for better geocoding
        formatted_parts = []
        if clean_address:
            formatted_parts.append(clean_address)
        if city:
            formatted_parts.append(city)
        if state:
            formatted_parts.append(state)
        if zip_code:
            formatted_parts.append(zip_code)
            
        return ", ".join(formatted_parts)
    
    def geocode(self, address, city, state, zip_code=None, max_attempts=3):
        """
        Geocode an address with multiple attempts and better formatting
        Returns a tuple (latitude, longitude) or None if geocoding fails
        """
        formatted_address = self.format_address(address, city, state, zip_code)
        print(f"Geocoding formatted address: {formatted_address}")
        
        # Multiple attempts with exponential backoff
        for attempt in range(max_attempts):
            try:
                # Add small delay between attempts (increases with each retry)
                if attempt > 0:
                    time.sleep(2 * attempt)
                
                location = self.geolocator.geocode(formatted_address)
                if location:
                    return (location.latitude, location.longitude)
                    
                # If primary attempt fails, try without zip code if present
                if attempt == 0 and zip_code:
                    simplified = self.format_address(address, city, state)
                    print(f"Primary geocoding failed. Trying without zip: {simplified}")
                    location = self.geolocator.geocode(simplified)
                    if location:
                        return (location.latitude, location.longitude)
                        
                # Try with just city and state on last attempt
                if attempt == max_attempts - 1:
                    city_state = f"{city}, {state}"
                    print(f"Trying with just city and state: {city_state}")
                    location = self.geolocator.geocode(city_state)
                    if location:
                        return (location.latitude, location.longitude)
                        
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                print(f"Geocoding attempt {attempt+1} failed with error: {str(e)}")
                continue
            except Exception as e:
                print(f"Unexpected geocoding error: {str(e)}")
                break
                
        print("All geocoding attempts failed")
        return None

# Create a singleton instance for reuse
geocoding_service = GeocodingService()