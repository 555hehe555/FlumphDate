from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from utils import load_json, get_weekday_name, is_time_in_range, get_weather, WEATHER_API_KEY

LESSONS = load_json('lessons.json')
HOLIDAYS = load_json('holidays.json')


class Scheduler:
    def __init__(self, bot, settings: dict):
        self.bot = bot
        self.settings = settings
        self.scheduler = AsyncIOScheduler()

    def start(self):
        # Перевірка уроків щохвилини
        self.scheduler.add_job(self.check_lessons, 'interval', minutes=1)
        # Дайджест що 5 хв для демо (замість раз на добу)
        self.scheduler.add_job(self.daily_digest, 'cron', hour='*', minute='00')
        self.scheduler.start()

    async def check_lessons(self):
        now = datetime.now()
        tnow = now.time()
        day = get_weekday_name(now)
        today_lessons = LESSONS['lessons'].get(day, [])
        times = LESSONS['time_lessons']
        for uid, conf in self.settings.items():
            for idx, interval in enumerate(times):
                start_str, end_str = interval.split('-')
                t_start = datetime.strptime(start_str, '%H:%M').time()
                t_end = datetime.strptime(end_str, '%H:%M').time()
                # старт уроку
                if conf['notify_start'] and tnow == t_start:
                    await self.bot.send_message(uid,
                                                f"Урок {idx + 1} розпочався: {today_lessons[idx] if idx < len(today_lessons) else '-'}")
                # за 3 хв до кінця
                if conf['notify_end'] and (datetime.combine(now.date(), t_end) - now) == timedelta(minutes=3):
                    await self.bot.send_message(uid, f"Урок {idx + 1} закінчиться через 3 хвилини")

    async def daily_digest(self):
        now = datetime.now()
        date_str = now.strftime('%d.%m.%Y')
        day = get_weekday_name(now)
        lat, lon = 50.45, 30.52  # Київ, наприклад; можна зберігати в налаштуваннях
        weather = await get_weather(lat, lon, WEATHER_API_KEY)
        for uid, conf in self.settings.items():
            if not conf.get('morning_digest'): continue
            # Збираємо текст дайджесту
            lessons = LESSONS['lessons'].get(day, [])
            hol = HOLIDAYS.get(now.strftime('%m-%d'), [])
            w = weather['hourly'][:24]
            temp_morning = w[6]['temp']
            temp_day = w[12]['temp']
            temp_evening = w[18]['temp']
            text = (
                f"<b>Дайджест на {date_str} ({day})</b>\n"
                f"Свята: {'; '.join(hol) if hol else 'немає'}\n"
                f"Уроки: {'; '.join(lessons) if lessons else 'Вихідний'}\n"
                f"Погода: ранок {temp_morning}°C, день {temp_day}°C, вечір {temp_evening}°C"
            )
            await self.bot.send_message(uid, text)
