from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import Tool
from huggingface_hub import list_models
import requests

# Export DuckDuckGoSearchRun directly for use
# Note: This will be used as DuckDuckGoSearchRun() in the importing file

def get_weather_info(location: str) -> str:
    """Fetches real weather information for a given location using Open-Meteo API."""
    try:
        # First, geocode the location to get coordinates
        geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geo_response = requests.get(geocoding_url)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        
        if not geo_data.get("results"):
            return f"Location '{location}' not found."
        
        # Get coordinates
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        city_name = geo_data["results"][0]["name"]
        country = geo_data["results"][0].get("country", "")
        
        # Get weather data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&temperature_unit=celsius"
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        # Parse current weather
        current = weather_data["current"]
        temp = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        feels_like = current["apparent_temperature"]
        wind_speed = current["wind_speed_10m"]
        weather_code = current["weather_code"]
        
        # Map weather codes to descriptions
        weather_descriptions = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }
        
        condition = weather_descriptions.get(weather_code, "Unknown")
        
        # Format the response
        location_str = f"{city_name}, {country}" if country else city_name
        return (f"Weather in {location_str}:\n"
                f"Condition: {condition}\n"
                f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
                f"Humidity: {humidity}%\n"
                f"Wind Speed: {wind_speed} km/h")
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"
    except KeyError as e:
        return f"Error parsing weather data: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def get_hub_stats(author: str) -> str:
    """Fetches the most downloaded model from a specific author on the Hugging Face Hub."""
    try:
        # List models from the specified author, sorted by downloads
        models = list(list_models(author=author, sort="downloads", direction=-1, limit=1))

        if models:
            model = models[0]
            return f"The most downloaded model by {author} is {model.id} with {model.downloads:,} downloads."
        else:
            return f"No models found for author {author}."
    except Exception as e:
        return f"Error fetching models for {author}: {str(e)}"

# Initialize the weather info tool
weather_info_tool = Tool(
    name="get_weather_info",
    func=get_weather_info,
    description="Fetches real-time weather information for a given location using Open-Meteo API."
)

# Initialize the hub stats tool
hub_stats_tool = Tool(
    name="get_hub_stats",
    func=get_hub_stats,
    description="Fetches the most downloaded model from a specific author on the Hugging Face Hub."
)