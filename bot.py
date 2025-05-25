# 🧩 ІМПОРТИ
import asyncio
import logging
import json
from datetime import datetime, time
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# 🔐 ТОКЕН
API_TOKEN = "6575633968:AAG1Ws6-MtOlMUR-S9Y3JbP6jvHzC8OIIN4"

# 🧾 ЛОГУВАННЯ
logging.basicConfig(level=logging.INFO)

# 🤖 ІНІЦІАЛІЗАЦІЯ БОТА
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ⌨️ ОСНОВНА КЛАВІАТУРА
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Розклад на сьогодні"), KeyboardButton(text="📆 Час уроків")],
        [KeyboardButton(text="🎉 Свята"), KeyboardButton(text="⚙️ Налаштування")],
        [KeyboardButton(text="🧹 Очистити чат")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Обери опцію 👇"
)


# 📁 ЗАГРУЗКА JSON-ФАЙЛІВ
def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

lessons_data = load_json("./data/lessons.json")
holidays_data = load_json("./data/holidays.json")
SETTINGS_FILE = "./data/user_settings.json"

# ⚙️ ЗБЕРЕЖЕННЯ/ЗАВАНТАЖЕННЯ НАЛАШТУВАНЬ
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

user_settings = load_settings()

# 🧠 НАЗВА ДНЯ ТИЖНЯ
def get_weekday_name():
    days = {
        0: "Понеділок",
        1: "Вівторок",
        2: "Середа",
        3: "Четверг",
        4: "П’ятниця",
        5: "Субота",
        6: "Неділя"
    }
    return days[datetime.now().weekday()]

# ⏰ ЧИ ЧАС В ДІАПАЗОНІ
def is_time_in_range(target_time_str: str, check_time: time = None) -> bool:
    try:
        start_str, end_str = target_time_str.split('-')
        start_t = datetime.strptime(start_str, "%H:%M").time()
        end_t = datetime.strptime(end_str, "%H:%M").time()
        current_t = check_time if check_time is not None else datetime.now().time()

        if start_t <= end_t:
            return start_t <= current_t <= end_t
        else:
            return current_t >= start_t or current_t <= end_t
    except ValueError:
        return False
    except Exception:
        return False

# 🚀 ОБРОБНИК /start
@dp.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer("Привіт! Це твій рофельний датник 🤖", reply_markup=main_kb)


# ⚙️ НАЛАШТУВАННЯ КОРИСТУВАЧА
def get_or_create_user_settings(user_id: str):
    if user_id not in user_settings:
        user_settings[user_id] = {
            "morning_digest": True,
            "sound_enabled": True,
            "lesson_end_notifications": True
        }
        save_settings(user_settings)
    return user_settings[user_id]


@dp.message(F.text == "⚙️ Налаштування")
async def settings_handler(message: Message):
    user_id = str(message.from_user.id)
    settings = settings = get_or_create_user_settings(user_id)


    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"Ранкова розсилка: {'✅' if settings['morning_digest'] else '❌'}",
            callback_data="toggle_morning"
        )],
        [InlineKeyboardButton(
            text=f"Звук: {'🔊' if settings['sound_enabled'] else '🔇'}",
            callback_data="toggle_sound"
        )],
        [InlineKeyboardButton(
            text=f"Повідомлення про кінець уроку: {'✅' if settings['lesson_end_notifications'] else '❌'}",
            callback_data="toggle_end_notify"
        )]
    ])
    await message.answer("Налаштування користувача ⚙️", reply_markup=keyboard)


# 🔁 ОБРОБНИК КНОПОК INLINE-КЛАВІАТУРИ (виправлено)
@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    settings = user_settings.get(user_id, {
        "morning_digest": True,
        "sound_enabled": True,
        "lesson_end_notifications": True
    })

    if callback.data == "toggle_morning":
        settings["morning_digest"] = not settings["morning_digest"]
    elif callback.data == "toggle_sound":
        settings["sound_enabled"] = not settings["sound_enabled"]
    elif callback.data == "toggle_end_notify":
        settings["lesson_end_notifications"] = not settings["lesson_end_notifications"]

    user_settings[user_id] = settings
    save_settings(user_settings)

    # Оновлюємо повідомлення на місці (без видалення)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"Ранкова розсилка: {'✅' if settings['morning_digest'] else '❌'}",
            callback_data="toggle_morning"
        )],
        [InlineKeyboardButton(
            text=f"Звук: {'🔊' if settings['sound_enabled'] else '🔇'}",
            callback_data="toggle_sound"
        )],
        [InlineKeyboardButton(
            text=f"Повідомлення про кінець уроку: {'✅' if settings['lesson_end_notifications'] else '❌'}",
            callback_data="toggle_end_notify"
        )]
    ])

    await callback.message.edit_text(
        "Налаштування користувача ⚙️",
        reply_markup=keyboard
    )
    await callback.answer("Оновлено ✅")


# 🧹 ОЧИСТКА ЧАТУ (нове виправлення)
@dp.message(F.text == "🧹 Очистити чат")
async def clear_chat(message: Message):
    chat_id = message.chat.id
    last_message_id = message.message_id  # Стартуємо з поточного повідомлення
    deleted_count = 0
    errors = 0

    await message.answer("Починаю очистку... ⏳")

    while errors < 50:  # Дозволяємо кілька помилок поспіль
        try:
            # Видаляємо повідомлення
            await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
            deleted_count += 1
            last_message_id -= 1  # Переходимо до попереднього повідомлення
            errors = 0  # Скидаємо лічильник помилок
            await asyncio.sleep(0.05)  # Затримка щоб не отримати ліміт Telegram API
        except Exception as e:
            if "message to delete not found" in str(e).lower():
                # Якщо повідомлення не знайдено - припиняємо
                break
            errors += 1
            last_message_id -= 1  # Пробуємо наступне
            continue

    await bot.send_message(
        chat_id=chat_id,
        text=f"Видалено {deleted_count} повідомлень. Чат очищено! 🧹",
        reply_markup=main_kb
    )


# 📅 РОЗКЛАД НА СЬОГОДНІ
@dp.message(F.text == "📅 Розклад на сьогодні")
async def today_schedule(message: Message):
    day = get_weekday_name()
    lessons = lessons_data["lessons"].get(day, [])
    if lessons:
        text = f"<b>{day}</b>\n" + "\n".join([f"{i + 1}. {lesson}" for i, lesson in enumerate(lessons)])
    else:
        text = f"<b>{day}</b>\nВихідний 😎"
    await message.answer(text)

# ⏰ ПОВНИЙ ЧАС УРОКІВ
@dp.message(F.text == "📆 Час уроків")
async def full_schedule(message: Message):
    text = "<b>Час уроків</b>\n"
    for i, time_l in enumerate(lessons_data["time_lessons"]):
        if is_time_in_range(time_l):
            text += f"{i + 1}: {time_l}     <b>🟢 зараз</b>\n"
        else:
            text += f"{i + 1}: {time_l}\n"
    await message.answer(text)

# 🎉 СВЯТА
@dp.message(F.text == "🎉 Свята")
async def today_holidays(message: Message):
    today = datetime.now().strftime("%m-%d")
    holidays = holidays_data.get(today, [])
    if holidays:
        text = "<b>Сьогодні свята:</b>\n" + "\n".join([f"🎉 {h}" for h in holidays])
    else:
        text = "Сьогодні без свят. Але настрій все одно 🔥"
    await message.answer(text)

# 🏁 ЗАПУСК
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
