import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from utils import load_settings, save_settings
from handlers import register_handlers
from scheduler import Scheduler

API_TOKEN = "6575633968:AAG1Ws6-MtOlMUR-S9Y3JbP6jvHzC8OIIN4"
WEATHER_API_KEY = "de72e8ee43448bdfbf0fac7046210d5a"

logging.basicConfig(level=logging.INFO)

async def main():
    # Ініціалізація
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Завантаження налаштувань користувачів
    user_settings = load_settings()

    # Реєстрація обробників
    register_handlers(dp, bot, user_settings)

    # Запуск шедулера
    scheduler = Scheduler(bot, user_settings)
    scheduler.start()

    # Полінг
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
