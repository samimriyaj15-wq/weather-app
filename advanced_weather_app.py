#!/usr/bin/env python3
""" Basic Weather App (Advanced Tier) """

import os
import io
import threading
from datetime import datetime
from collections import defaultdict

import requests

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    raise SystemExit("tkinter is required. On Debian/Ubuntu: sudo apt-get install python3-tk")

try:
    from PIL import Image, ImageTk
except ImportError:
    raise SystemExit("Pillow is required. Install with: pip install pillow")


API_KEY = os.environ.get("OPENWEATHER_API_KEY", "PASTE_YOUR_API_KEY_HERE")
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_URL_TEMPLATE = "https://openweathermap.org/img/wn/{icon}@2x.png"
IPINFO_URL = "https://ipinfo.io/json"
REQUEST_TIMEOUT = 8


def c_to_f(c: float) -> float:
    return (c * 9 / 5) + 32


class WeatherAPIError(Exception):
    """Raised for expected, user-facing API problems (bad city, bad key, etc.)."""


def fetch_current(location: str) -> dict:
    params = {"appid": API_KEY, "units": "metric"}
    if location.replace(" ", "").isdigit():
        params["zip"] = location
    else:
        params["q"] = location
    resp = requests.get(CURRENT_URL, params=params, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 401:
        raise WeatherAPIError("Invalid API key. Check OPENWEATHER_API_KEY (new keys take ~15 min to activate).")
    if resp.status_code == 404:
        raise WeatherAPIError(f"Location '{location}' not found.")
    resp.raise_for_status()
    return resp.json()


def fetch_forecast(location: str) -> dict:
    params = {"appid": API_KEY, "units": "metric"}
    if location.replace(" ", "").isdigit():
        params["zip"] = location
    else:
        params["q"] = location
    resp = requests.get(FORECAST_URL, params=params, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 401:
        raise WeatherAPIError("Invalid API key. Check OPENWEATHER_API_KEY (new keys take ~15 min to activate).")
    if resp.status_code == 404:
        raise WeatherAPIError(f"Location '{location}' not found.")
    resp.raise_for_status()
    return resp.json()


def detect_location_from_ip() -> str:
    """Uses ipinfo.io to guess a 'City,CountryCode' string from the public IP."""
    resp = requests.get(IPINFO_URL, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    city = data.get("city")
    country = data.get("country")
    if not city:
        raise WeatherAPIError("Could not determine location from IP address.")
    return f"{city},{country}" if country else city


def fetch_icon_image(icon_code: str, size=(50, 50)):
    """Downloads a weather icon and returns a Tkinter-compatible PhotoImage."""
    url = ICON_URL_TEMPLATE.format(icon=icon_code)
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather App")
        self.geometry("760x560")
        self.minsize(700, 520)
        self.configure(bg="#eef3f7")

        # State
        self.units = "C"  # or "F"
        self.current_data = None      
        self.forecast_data = None     
        self._icon_refs = []          

        self._build_layout()

        if API_KEY == "PASTE_YOUR_API_KEY_HERE" or not API_KEY:
            self._show_error(
                "No API key configured. Set OPENWEATHER_API_KEY or edit API_KEY in this file."
            )

    def _build_layout(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        
        top = tk.Frame(self, bg="#eef3f7", pady=10)
        top.pack(fill="x", padx=12)

        tk.Label(top, text="City or ZIP:", bg="#eef3f7", font=("Helvetica", 11)).pack(side="left")
        self.city_entry = ttk.Entry(top, font=("Helvetica", 11), width=28)
        self.city_entry.pack(side="left", padx=(6, 10))
        self.city_entry.bind("<Return>", lambda e: self.on_get_weather())

        ttk.Button(top, text="Get Weather", command=self.on_get_weather).pack(side="left", padx=4)
        ttk.Button(top, text="📍 Use My Location", command=self.on_detect_location).pack(side="left", padx=4)

        self.unit_btn = ttk.Button(top, text="Show °F", command=self.on_toggle_units)
        self.unit_btn.pack(side="right")

        
        self.error_var = tk.StringVar(value="")
        self.error_label = tk.Label(
            self, textvariable=self.error_var, bg="#fdecea", fg="#b3261e",
            font=("Helvetica", 10, "bold"), pady=6
        )
        

        
        current_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        current_frame.pack(fill="x", padx=12, pady=(4, 10))

        self.icon_label = tk.Label(current_frame, bg="white")
        self.icon_label.grid(row=0, column=0, rowspan=3, padx=14, pady=10)

        self.city_var = tk.StringVar(value="Enter a location above to begin")
        tk.Label(current_frame, textvariable=self.city_var, bg="white",
                 font=("Helvetica", 16, "bold")).grid(row=0, column=1, sticky="w", pady=(10, 0))

        self.temp_var = tk.StringVar(value="")
        tk.Label(current_frame, textvariable=self.temp_var, bg="white",
                 font=("Helvetica", 26, "bold"), fg="#1a73e8").grid(row=1, column=1, sticky="w")

        self.details_var = tk.StringVar(value="")
        tk.Label(current_frame, textvariable=self.details_var, bg="white",
                 font=("Helvetica", 10), justify="left").grid(row=2, column=1, sticky="w", pady=(0, 10))

        
        tk.Label(self, text="Next Hours", bg="#eef3f7", font=("Helvetica", 12, "bold")).pack(
            anchor="w", padx=14
        )
        self.hourly_frame = tk.Frame(self, bg="#eef3f7")
        self.hourly_frame.pack(fill="x", padx=12, pady=(2, 10))

        # --- Daily forecast panel --------------------------------------------
        tk.Label(self, text="Next 5 Days", bg="#eef3f7", font=("Helvetica", 12, "bold")).pack(
            anchor="w", padx=14
        )
        self.daily_frame = tk.Frame(self, bg="#eef3f7")
        self.daily_frame.pack(fill="x", padx=12, pady=(2, 10))


    def _show_error(self, message: str):
        self.error_var.set("⚠ " + message)
        self.error_label.pack(fill="x", padx=12, pady=(0, 6))

    def _clear_error(self):
        self.error_var.set("")
        self.error_label.pack_forget()


    def on_get_weather(self):
        location = self.city_entry.get().strip()
        if not location:
            self._show_error("Please enter a city name or ZIP code.")
            return
        self._clear_error()
        self._run_async(lambda: self._load_weather(location))

    def on_detect_location(self):
        self._clear_error()

        def task():
            try:
                location = detect_location_from_ip()
            except WeatherAPIError as e:
                self.after(0, lambda: self._show_error(str(e)))
                return
            except requests.exceptions.RequestException:
                self.after(0, lambda: self._show_error("Could not reach the location-detection service."))
                return
            self.after(0, lambda: self.city_entry.delete(0, tk.END))
            self.after(0, lambda: self.city_entry.insert(0, location))
            self._load_weather(location)

        threading.Thread(target=task, daemon=True).start()

    def on_toggle_units(self):
        self.units = "F" if self.units == "C" else "C"
        self.unit_btn.config(text=f"Show °{'C' if self.units == 'F' else 'F'}")
        if self.current_data and self.forecast_data:
            self._render_current(self.current_data)
            self._render_hourly(self.forecast_data)
            self._render_daily(self.forecast_data)


    def _run_async(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _load_weather(self, location: str):
        try:
            current = fetch_current(location)
            forecast = fetch_forecast(location)
        except WeatherAPIError as e:
            self.after(0, lambda: self._show_error(str(e)))
            return
        except requests.exceptions.Timeout:
            self.after(0, lambda: self._show_error("Request timed out. Check your internet connection."))
            return
        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self._show_error("Could not connect to the weather service."))
            return
        except requests.exceptions.RequestException as e:
            self.after(0, lambda: self._show_error(f"Network error: {e}"))
            return

        self.current_data = current
        self.forecast_data = forecast
        self.after(0, self._clear_error)
        self.after(0, lambda: self._render_current(current))
        self.after(0, lambda: self._render_hourly(forecast))
        self.after(0, lambda: self._render_daily(forecast))

    def _fmt_temp(self, celsius: float) -> str:
        if self.units == "F":
            return f"{c_to_f(celsius):.1f}°F"
        return f"{celsius:.1f}°C"

    def _render_current(self, data: dict):
        name = data.get("name", "Unknown")
        country = data.get("sys", {}).get("country", "")
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})

        self.city_var.set(f"{name}, {country}")
        self.temp_var.set(self._fmt_temp(main.get("temp", 0)))
        self.details_var.set(
            f"{weather.get('description', '').title()}\n"
            f"Feels like {self._fmt_temp(main.get('feels_like', 0))}   |   "
            f"Humidity {main.get('humidity', 'N/A')}%   |   "
            f"Wind {wind.get('speed', 'N/A')} m/s"
        )

        icon_code = weather.get("icon")
        if icon_code:
            self._set_icon_async(self.icon_label, icon_code, (70, 70))

    def _set_icon_async(self, label: tk.Label, icon_code: str, size):
        def task():
            try:
                photo = fetch_icon_image(icon_code, size)
            except requests.exceptions.RequestException:
                return
            def apply():
                self._icon_refs.append(photo)
                label.config(image=photo)
            self.after(0, apply)
        threading.Thread(target=task, daemon=True).start()

    def _clear_frame(self, frame: tk.Frame):
        for child in frame.winfo_children():
            child.destroy()

    def _render_hourly(self, forecast: dict):
        self._clear_frame(self.hourly_frame)
        entries = forecast.get("list", [])[:6]  
        for entry in entries:
            card = tk.Frame(self.hourly_frame, bg="white", bd=1, relief="solid", padx=8, pady=6)
            card.pack(side="left", padx=4, expand=True, fill="both")

            dt = datetime.fromtimestamp(entry["dt"])
            tk.Label(card, text=dt.strftime("%H:%M"), bg="white", font=("Helvetica", 10, "bold")).pack()

            icon_label = tk.Label(card, bg="white")
            icon_label.pack()
            icon_code = entry.get("weather", [{}])[0].get("icon")
            if icon_code:
                self._set_icon_async(icon_label, icon_code, (36, 36))

            temp = entry.get("main", {}).get("temp", 0)
            tk.Label(card, text=self._fmt_temp(temp), bg="white", font=("Helvetica", 10)).pack()

    def _render_daily(self, forecast: dict):
        self._clear_frame(self.daily_frame)


        by_day = defaultdict(list)
        for entry in forecast.get("list", []):
            dt = datetime.fromtimestamp(entry["dt"])
            by_day[dt.date()].append((dt, entry))

        days = sorted(by_day.keys())[:5]
        for day in days:
            slots = by_day[day]
            
            best = min(slots, key=lambda pair: abs(pair[0].hour - 12))
            dt, entry = best

            card = tk.Frame(self.daily_frame, bg="white", bd=1, relief="solid", padx=8, pady=6)
            card.pack(side="left", padx=4, expand=True, fill="both")

            tk.Label(card, text=dt.strftime("%a %m/%d"), bg="white",
                     font=("Helvetica", 10, "bold")).pack()

            icon_label = tk.Label(card, bg="white")
            icon_label.pack()
            icon_code = entry.get("weather", [{}])[0].get("icon")
            if icon_code:
                self._set_icon_async(icon_label, icon_code, (36, 36))

            temp = entry.get("main", {}).get("temp", 0)
            tk.Label(card, text=self._fmt_temp(temp), bg="white", font=("Helvetica", 10)).pack()
            tk.Label(card, text=entry.get("weather", [{}])[0].get("main", ""),
                     bg="white", font=("Helvetica", 9)).pack()


def main():
    app = WeatherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
