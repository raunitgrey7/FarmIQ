import requests
import os
from dotenv import load_dotenv
load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "a1ebb70e1acc402d941200642250207")  # replace or load securely


async def get_weather_data(lat: float, lon: float):
    API_KEY = os.getenv("WEATHER_API_KEY", "a1ebb70e1acc402d941200642250207")
    url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={lat},{lon}&aqi=no"
    
    print("Weather API URL:", url)  # ✅ NOW it's safe — inside the function

    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or "error" in data:
        raise Exception(data.get("error", {}).get("message", "Weather API Error"))

    return {
        "location": data["location"]["name"],
        "region": data["location"]["region"],
        "country": data["location"]["country"],
        "temperature_c": data["current"]["temp_c"],
        "humidity": data["current"]["humidity"],
        "wind_kph": data["current"]["wind_kph"],
        "condition": data["current"]["condition"]["text"],
        "icon": data["current"]["condition"]["icon"]
    }
