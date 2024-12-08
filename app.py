from flask import Flask, render_template, request
import requests
import json

API_KEY = "XzKIblRO445awcuauGkULV8S3lzcAQLS"
LOCATION_URL = "http://dataservice.accuweather.com/locations/v1/cities/autocomplete"
FIVE_DAY_FORECAST_URL = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/{}"

app = Flask(__name__)

# Функция для получения координат города
def get_location_key(city_name):
    params = {
        "apikey": API_KEY,
        "q": city_name
    }
    try:
        response = requests.get(LOCATION_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]["Key"]
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к AccuWeather Location API: {e}")
        return None
    except (IndexError, KeyError) as e: 
        print(f"Ошибка при обработке данных Location API: {e}")
        return None

# Функция для получения данных о погоде с OpenWeatherMap API
def get_weather_data(location_key):
    try:
        response = requests.get(FIVE_DAY_FORECAST_URL.format(location_key), params={"apikey": API_KEY, "metric": True})
        response.raise_for_status()
        data = response.json()
        if data and "DailyForecasts" in data and data["DailyForecasts"]:
            return data["DailyForecasts"][0] #  Данные для первого дня из 5-дневного прогноза
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к AccuWeather Forecast API: {e}")
        return None
    except (IndexError, KeyError) as e:
        print(f"Ошибка обработки данных Forecast API: {e}")
        return None


# Модель для оценки неблагоприятных погодных условий
def check_bad_weather(weather_data):
    if not weather_data:
        return "Нет данных о погоде"

    try:
        temperature_max = weather_data["Temperature"]["Maximum"]["Value"]
        temperature_min = weather_data["Temperature"]["Minimum"]["Value"]
        wind_speed_day = weather_data.get("Day", {}).get("Wind", {}).get("Speed", {}).get("Value", 0)
        wind_speed_night = weather_data.get("Night", {}).get("Wind", {}).get("Speed", {}).get("Value", 0)
        precipitation_day = weather_data.get("Day", {}).get("HasPrecipitation", False)
        precipitation_night = weather_data.get("Night", {}).get("HasPrecipitation", False)

        print(f"Температура (макс): {temperature_max}, Температура (мин): {temperature_min}")
        print(f"Скорость ветра (день): {wind_speed_day}, Скорость ветра (ночь): {wind_speed_night}")
        print(f"Осадки (день): {precipitation_day}, Осадки (ночь): {precipitation_night}")

        if temperature_max > 30 or temperature_min < -5:
            return "Ой-ой, погода плохая (температура)"
        if wind_speed_day > 10 or wind_speed_night > 10:
            return "Ой-ой, погода плохая (ветер)"
        if precipitation_day or precipitation_night:
            return "Ой-ой, погода плохая (осадки)"

    except KeyError as e:
        print(f"Ошибка: в данных о погоде нет ключа {e}: {weather_data}")
        return "Недостаточно данных о погоде"

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

        start_location_key = get_location_key(start_city)
        end_location_key = get_location_key(end_city)

        if not start_location_key or not end_location_key:
            weather_status = "Не удалось определить местоположение одного или обоих городов."
            return render_template("index.html", weather_status=weather_status)

        start_weather_data = get_weather_data(start_location_key)
        end_weather_data = get_weather_data(end_location_key)
    
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








if __name__ == "__main__":
    app.run(debug=True)
