import json
import os
from datetime import datetime, time

# Шляхи до файлів
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
SETTINGS_FILE = os.path.join(DATA_DIR, 'user_settings.json')


# Завантажити JSON із data/
def load_json(filename: str):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


WEATHER_API_KEY = "c6d273877e1d60f1c2bd0ebe53eff878"


# Завантажити/зберегти налаштування
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_settings(settings: dict):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# Перевірити, чи зараз у часовому проміжку "HH:MM-HH:MM"
def is_time_in_range(interval: str, now: time = None) -> bool:
    try:
        start_str, end_str = interval.split('-')
        t1 = datetime.strptime(start_str, '%H:%M').time()
        t2 = datetime.strptime(end_str, '%H:%M').time()
        current = now or datetime.now().time()
        if t1 <= t2:
            return t1 <= current <= t2
        return current >= t1 or current <= t2
    except:
        return False


# Назва дня тижня
def get_weekday_name(dt: datetime = None) -> str:
    days = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П’ятниця', 'Субота', 'Неділя']
    idx = (dt or datetime.now()).weekday()
    return days[idx]


# Витягнути погоду (приклад для OpenWeather)
import aiohttp


async def get_weather(lat: float, lon: float, api_key: str) -> dict:
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}&lang=uk"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()



