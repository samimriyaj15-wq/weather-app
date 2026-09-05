# Weather-app
 Weather App
#  Weather App

Two implementations, matching the Beginner and Advanced tiers.

## 1. Get a free API key
1. Go to https://openweathermap.org/api and create a free account.
2. Grab your API key from the "API keys" tab.
3. **New keys can take up to ~10-15 minutes to activate** — if you get a
   401 error right away, wait a bit and try again.

## 2. Provide the key to the app
Either export it as an environment variable (recommended, keeps it out of your code):

```bash
export OPENWEATHER_API_KEY="your_key_here"
```

...or open either `.py` file and paste it directly into the `API_KEY = ...` line.

## 3. Install dependencies

```bash
pip install requests
# Advanced tier only:
pip install pillow
```

## 4. Run

**Beginner (command-line):**
```bash
python beginner_weather_app.py
```
Prompts for a city name or ZIP code, then prints temperature (°C/°F),
humidity, condition, and wind speed. Handles bad input, city-not-found,
invalid key, and network timeouts gracefully.

**Advanced (GUI):**
```bash
python advanced_weather_app.py
```
- Enter a city/ZIP and click **Get Weather**, or click **📍 Use My Location**
  to auto-detect your city via your public IP (ipinfo.io).
- Shows current conditions with an icon, a 6-slot hourly-style forecast, and
  a 5-day forecast.
- **Show °F / Show °C** toggles units across all panels instantly.
- All errors appear as a banner inside the window — nothing is printed to
  the terminal.

### A note on "hourly" forecasts
OpenWeatherMap's free tier only offers a 3-hour-interval, 5-day forecast
endpoint (no true per-hour endpoint). The hourly panel uses the next 6
of those 3-hour slots (~18 hours out), and the daily panel picks the
reading closest to noon for each of the next 5 days.
