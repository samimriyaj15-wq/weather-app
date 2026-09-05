#!/usr/bin/env python3
""""Basic Weather App 
    A command-line tool that fetches and displays real-time weather data for a user-specified city or ZIP code using the OpenWeatherMap API. """

import os
import sys
import json
import requests

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "PASTE_YOUR_API_KEY_HERE")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = 8  


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9 / 5) + 32


def get_weather(location: str) -> dict:
    """
    Calls the OpenWeatherMap 'current weather' endpoint for the given
    location (city name, "City,CountryCode", or ZIP code like "94040,us").

    Returns the parsed JSON dict on success.
    Raises requests.exceptions.* or ValueError on failure so the caller
    can present a friendly message.
    """
   
    if location.replace(" ", "").isdigit():
        params = {"zip": location, "appid": API_KEY, "units": "metric"}
    else:
        params = {"q": location, "appid": API_KEY, "units": "metric"}

    response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)

    if response.status_code == 401:
        raise ValueError(
            "Invalid API key. Double-check OPENWEATHER_API_KEY / API_KEY, "
            "and note new keys can take up to ~15 minutes to activate."
        )
    if response.status_code == 404:
        raise ValueError(f"Location '{location}' not found. Check the spelling or ZIP code.")

    response.raise_for_status()  
    return response.json()


def display_weather(data: dict) -> None:
    """Pretty-prints the relevant fields from the OpenWeatherMap response."""
    city = data.get("name", "Unknown")
    country = data.get("sys", {}).get("country", "")
    main = data.get("main", {})
    weather_list = data.get("weather", [{}])
    wind = data.get("wind", {})

    temp_c = main.get("temp")
    feels_like_c = main.get("feels_like")
    humidity = main.get("humidity")
    description = weather_list[0].get("description", "N/A").title()
    wind_speed = wind.get("speed")  

    temp_f = celsius_to_fahrenheit(temp_c) if temp_c is not None else None
    feels_f = celsius_to_fahrenheit(feels_like_c) if feels_like_c is not None else None

    print("\n" + "=" * 42)
    print(f"  Weather for {city}, {country}")
    print("=" * 42)
    if temp_c is not None:
        print(f"  Temperature : {temp_c:.1f}°C  /  {temp_f:.1f}°F")
    if feels_like_c is not None:
        print(f"  Feels like  : {feels_like_c:.1f}°C  /  {feels_f:.1f}°F")
    print(f"  Condition   : {description}")
    print(f"  Humidity    : {humidity}%")
    if wind_speed is not None:
        print(f"  Wind speed  : {wind_speed} m/s")
    print("=" * 42 + "\n")


def prompt_for_location() -> str:
    """Keeps asking until the user provides a non-empty location string."""
    while True:
        location = input("Enter a city name or ZIP code (e.g. 'London' or '94040,us'): ").strip()
        if location:
            return location
        print(" Input cannot be empty. Please try again.\n")


def main() -> None:
    print("Basic Weather App — Beginner Tier")

    if API_KEY == "PASTE_YOUR_API_KEY_HERE" or not API_KEY:
        print(
            "  No API key configured. Set the OPENWEATHER_API_KEY environment "
            "variable or edit API_KEY in this file before running.\n"
        )
        sys.exit(1)

    while True:
        location = prompt_for_location()
        try:
            data = get_weather(location)
            display_weather(data)
        except ValueError as e:
            
            print(f"\n✗ {e}\n")
        except requests.exceptions.Timeout:
            print("\n✗ The request timed out. Check your internet connection and try again.\n")
        except requests.exceptions.ConnectionError:
            print("\n✗ Could not connect to the weather service. Check your internet connection.\n")
        except requests.exceptions.RequestException as e:
            print(f"\n✗ An unexpected network error occurred: {e}\n")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"\n✗ Received an unexpected response from the server: {e}\n")

        again = input("Look up another location? (y/n): ").strip().lower()
        if again != "y":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
