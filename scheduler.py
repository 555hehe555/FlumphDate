from datetime import datetime, timedelta, time

from handlers import HOLIDAYS
from utils import get_weekday_name, load_json, load_settings, WEATHER_API_KEY, get_weather
from apscheduler.schedulers.asyncio import AsyncIOScheduler

LESSONS = load_json('lessons.json')
HOLIDAYS = load_json('holidays.json')

def is_same_minute(t1: time, t2: time):
    return t1.hour == t2.hour and t1.minute == t2.minute

class Scheduler:
    def __init__(self, bot, settings: dict):
        self.bot = bot
        self.settings = settings
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.add_job(self.check_lessons, 'interval', minutes=1)
        self.scheduler.add_job(self.maybe_send_digest, 'interval', minutes=1)
        self.scheduler.start()

    async def check_lessons(self):
        now = datetime.now()
        tnow = now.time()
        day = get_weekday_name(now)
        today_lessons = LESSONS['lessons'].get(day, [])
        times = LESSONS['time_lessons']

        # Оновлюємо налаштування користувачів перед перевіркою
        self.settings = load_settings()

        for uid, conf in self.settings.items():
            for idx, interval in enumerate(times):
                try:
                    start_str, end_str = interval.split('-')
                    t_start = datetime.strptime(start_str, '%H:%M').time()
                    t_end = datetime.strptime(end_str, '%H:%M').time()

                    # Повідомлення про початок уроку
                    if conf.get('notify_start') and is_same_minute(tnow, t_start):
                        text = f"⏰ Урок {idx + 1} розпочався: {today_lessons[idx] if idx < len(today_lessons) else '-'}"
                        await self.bot.send_message(uid, text)

                    # Повідомлення за 3 хв до кінця
                    if conf.get('notify_end'):
                        lesson_end = datetime.combine(now.date(), t_end)
                        if 0 <= (lesson_end - now).total_seconds() < 60:
                            text = f"⏳ Урок {idx + 1} закінчиться через 3 хвилини"
                            await self.bot.send_message(uid, text)
                except Exception as e:
                    print(f"[!] Помилка в інтервалі уроку {interval}: {e}")

    async def maybe_send_digest(self):
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        for uid, conf in self.settings.items():
            if not conf.get('morning_digest'):
                continue
            if current_time == conf.get('morning_time', '06:00'):
                await self.daily_digest(uid, now)

    async def daily_digest(self, uid: str, now: datetime = None):
        now = now or datetime.now()
        date_str = now.strftime('%d.%m.%Y')
        day = get_weekday_name(now)
        lat, lon = 50.11171, 27.03467
        try:
            weather = await get_weather(lat, lon, WEATHER_API_KEY)
            temp = weather['main']['temp']
            desc = weather['weather'][0]['description'].capitalize()
        except:
            temp = '?'
            desc = 'Невідомо'

        lessons = LESSONS['lessons'].get(day, [])
        hol = HOLIDAYS.get(now.strftime('%m-%d'), [])
        text = (
            f"<b>Дайджест на {date_str} ({day})</b>\n"
            f"Свята: {'; '.join(hol) if hol else 'немає'}\n"
            f"Уроки: {'; '.join(lessons) if lessons else 'Вихідний'}\n"
            f"Погода: {desc}, {temp}°C"
        )
        await self.bot.send_message(uid, text)

