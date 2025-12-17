import aiohttp
import json

"""
Weather API Module

Handles US weather forecast retrieval using:
- Nominatim (OpenStreetMap) for geocoding city names
- National Weather Service API for forecast data

Provides formatted weather forecasts with city and state information.
"""

# === Helper Function for API Requests ===
async def fetch_json(session, url, headers = None, params = None):
    # Generic async function to fetch JSON data from a URL
    async with session.get(url, headers = headers, params = params) as response:
        # If its not exactly 200, assume failure or unexpected format
        if response.status != 200:
            # Print error for debugging
            response_text = await response.text()
            print(f"Error {response.status} from {url}: {response_text[:100]}...")
            return None
        try:
            return await response.json()
        except aiohttp.ContentTypeError:
            # Fallback if the status is 200 but the body is not JSON, rarely happens
            print(f"Error: Status 200, but response body was not valid JSON from {url}.")
            return None

async def get_weather_data(city_name: str):
    """
    Handle the 3-step process: Geocoding -> Gridpoint -> Forecast
    Returns the forecast text or an error message
    """
    # Required User-Agent for Nominatim (Geocoding) and NWS (National Weather Service)
    HEADERS = {'User-Agent': 'Bugg_Bot/1.0 (cooperehuntington@gmail.com)'}

    async with aiohttp.ClientSession(headers = HEADERS) as session:
        # Step 1 Nominatim (City -> Lat/Lon)
        nominatim_url = 'https://nominatim.openstreetmap.org/search'
        nominatim_params = {'q': city_name, 'format': 'json', 'limit': 1, 'countrycodes': 'us', 'addressdetails': 1}

        geocode_data = await fetch_json(session, nominatim_url, params = nominatim_params)

        if not geocode_data: # Checking for an empty list/data
            return f"I couldn't locate **{city_name}** in the United States. Make sure it's spelled correctly and is a US city!"

        # JSON Parsing
        first_result = geocode_data[0]
        address = first_result.get('address', {})

        # Get City (Try city -> town -> village -> fallback to input)
        city = address.get('city') or address.get('town') or address.get('village') or city_name

        # Get State
        state = address.get('state', '')
        
        # Force "City, State" format
        if state:
            location_display = f"{city}, {state}"
        else:
            location_display = city
        
        # Get coordinates
        latitude = first_result.get('lat')
        longitude = first_result.get('lon')

        if not latitude and longitude:
            return f"Could not retrieve coordinates for **{city_name}**"
        
        # Step 2 NWS Gridpoint (Lat/Lon -> Forecast URL)'
        nws_grid_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        grid_data = await fetch_json(session, nws_grid_url)

        if not grid_data or 'properties' not in grid_data:
            return f"National Weather Service data unavailable for {city_name}."

        if 'forecast' not in grid_data['properties']:
            return f"National Weather Service data available, but no forecast URL found for this location."

        forecast_url = grid_data['properties']['forecast']

        # Step 3 NWS Final Forecast Request
        forecast_data = await fetch_json(session, forecast_url)

        if not forecast_data or 'periods' not in forecast_data.get('properties', {}):
            return f"Final forecast data could not be retrieved."
        
        # JSON parsing extract the first period's detailed forecast
        first_period = forecast_data['properties']['periods'][0]

        # You get the name (e.g. "Tonight") and the forecast text
        period_name = first_period.get('name', 'Forecast Period')
        detailed_forecast = first_period.get('detailedForecast', 'No detailed forecast available.')

        # Final output
        return (f"**Forecast for {period_name} near {location_display}**: \n"
                f"{detailed_forecast}")
