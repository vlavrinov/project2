from flask import Flask, render_template, request
import requests
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

API_KEY = "ae999113c2c98da99173260e9abccf58"
URL = "https://api.openweathermap.org/data/2.5/"

app = Flask(__name__)

# Функция для получения координат города
def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="weather_app")
    try:
        location = geolocator.geocode(city_name, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        return None, None
    except Exception as e:
        print(f"Ошибка получения координат: {e}")
        return None, None

# Функция для получения данных о погоде с OpenWeatherMap API
def get_weather_data(latitude, longitude):
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric",
    }
    try:
        response = requests.get(f"{URL}weather", params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к OpenWeatherMap API: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Ошибка при обработке данных от API: {e}")
        return None

# Модель для оценки неблагоприятных погодных условий
def check_bad_weather(weather_data):
    if not weather_data:
        return "Нет данных о погоде"

    try:
        temperature = weather_data["main"]["temp"]
        wind_speed = weather_data["wind"]["speed"]
        # Используем данные о дожде или снеге, если они есть
        rain = weather_data.get("rain", {}).get("1h", 0)
        snow = weather_data.get("snow", {}).get("1h", 0)
        # Если есть данные о дожде и снеге, берем максимальное значение
        precipitation = max(rain, snow)
        humidity = weather_data["main"]["humidity"]

    except KeyError as e:
        print(f"Ошибка: в данных о погоде нет ключа {e}")
        return "Недостаточно данных о погоде"

    if temperature < 0 or temperature > 35:
        return "Ой-ой, погода плохая (температура)"
    if wind_speed > 15: 
        return "Ой-ой, погода плохая (ветер)"
    if precipitation > 0.5: 
        return "Ой-ой, погода плохая (осадки)"
    if humidity > 80:
        return "Ой-ой, погода плохая (влажность)"
    return "Погода — супер"

# Обработчик главной страницы
@app.route("/", methods=["GET", "POST"])
def index():
    weather_status = None
    if request.method == "POST":
        start_city = request.form.get("start_city")
        end_city = request.form.get("end_city")

        if not start_city or not end_city:
            weather_status = "Пожалуйста, введите названия обоих городов."
            return render_template("index.html", weather_status=weather_status)
    
        # Получение координат для начального и конечного городов
        start_lat, start_lon = get_coordinates(start_city)
        end_lat, end_lon = get_coordinates(end_city)
    
        if start_lat is None or end_lat is None:
            weather_status = "Не удалось определить координаты одного или обоих городов. Пожалуйста, проверьте правильность написания."
            return render_template("index.html", weather_status=weather_status)
    
        # Получение данных о погоде для начального и конечного городов
        start_weather_data = get_weather_data(start_lat, start_lon)
        end_weather_data = get_weather_data(end_lat, end_lon)
    
        # Оценка погодных условий для начального и конечного городов
        start_weather_status = check_bad_weather(start_weather_data)
        end_weather_status = check_bad_weather(end_weather_data)
        
        weather_data_for_display = {
            "start_city": start_city,
            "start_weather": start_weather_data,
            "start_status": start_weather_status,
            "end_city": end_city,
            "end_weather": end_weather_data,
            "end_status": end_weather_status
        }
        return render_template("result.html", weather_data=weather_data_for_display)

    return render_template("index.html", weather_status=weather_status)

# Запуск приложения
if __name__ == "__main__":
    app.run(debug=True)