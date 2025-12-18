import aiohttp
import os

"""
Bugg Bot - NASA API Integration Module

Provides access to NASA's Astronomy Picture of the Day (APOD) service.

Features:
- Fetch daily astronomy images with explanations
- Optional date parameter (YYYY-MM-DD format) for historical images
- Handles NASA API server errors gracefully
- Returns image URLs and formatted descriptions

Main Function:
- get_apod(date=None): Returns (image_url, formatted_text)

Requires NASA_API_KEY environment variable.
API Documentation: https://api.nasa.gov/
"""

NASA_API_KEY = os.getenv("NASA_API_KEY")

async def get_apod(date=None):
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    # Add date parameter if provided
    if date:
        url += f"&date={date}"

    try:
        async with aiohttp.ClientSession() as session:
            # Set a timeout so the bot doesn't freeze waiting for NASA
            async with session.get(url, timeout=5) as response:
                
                # Handle NASA server issues (500-level errors)
                if response.status in [500, 502, 503, 504]:
                    return None, "🚫 **NASA API is down.** They are having server issues right now."
                
                # Handle forbidden access - usually means bad API key
                if response.status == 403:
                    return None, "🚫 **API Key Error.** Check your NASA API key."

                # Success - parse and return the data
                if response.status == 200:
                    data = await response.json()
                    title = data.get("title", "Space Image")
                    explanation = data.get("explanation", "No description.")
                    image_url = data.get("url")
                    return image_url, f"**{title}**\n{explanation}"
                
                # Catch any other unexpected status codes
                return None, f"⚠️ NASA returned status code: {response.status}"

    except Exception as e:
        # Connection errors, timeouts, or network issues
        print(f"NASA API Error: {e}")
        return None, "🚫 **Connection Error.** Could not reach NASA."