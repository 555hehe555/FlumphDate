# 📁 handlers/settings.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json, os

router = Router()

SETTINGS_PATH = "data/user_settings.json"

DEFAULT_SETTINGS = {
    "daily_digest": True,
    "sound": True,
    "notify_lesson_start": True,
    "notify_lesson_end": True,
    "notify_weather": True,
    "notify_cleanup": False,
    "location": "Kyiv"
}

def load_settings(user_id: int) -> dict:
    if not os.path.exists(SETTINGS_PATH):
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w") as f:
            json.dump({}, f)
    with open(SETTINGS_PATH, "r") as f:
        data = json.load(f)
    return data.get(str(user_id), DEFAULT_SETTINGS.copy())

def save_settings(user_id: int, settings: dict):
    with open(SETTINGS_PATH, "r") as f:
        data = json.load(f)
    data[str(user_id)] = settings
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)

def build_settings_keyboard(settings: dict) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for key, name in [
        ("daily_digest", "☀️ Щоденне зведення"),
        ("sound", "🔇 Звук"),
        ("notify_lesson_start", "🕐 Початок уроку"),
        ("notify_lesson_end", "⏰ Кінець уроку"),
        ("notify_weather", "🌦 Погода"),
        ("notify_cleanup", "🧹 Очищення чату")
    ]:
        status = "✅" if settings.get(key, False) else "❌"
        builder.button(text=f"{name}: {status}", callback_data=f"toggle:{key}")
    builder.button(text="📍 Змінити місто", callback_data="change_location")
    builder.button(text="🔙 Назад", callback_data="back")
    builder.adjust(1)
    return builder

@router.message(F.text.lower() == "налаштування")
async def settings_handler(msg: Message):
    settings = load_settings(msg.from_user.id)
    kb = build_settings_keyboard(settings).as_markup()
    await msg.answer("🔧 *Налаштування бота:*", reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("toggle:"))
async def toggle_setting(callback: CallbackQuery):
    key = callback.data.split(":")[1]
    user_id = callback.from_user.id
    settings = load_settings(user_id)
    settings[key] = not settings.get(key, False)
    save_settings(user_id, settings)
    kb = build_settings_keyboard(settings).as_markup()
    await callback.message.edit_text("🔧 *Налаштування бота:*", reply_markup=kb, parse_mode="Markdown")
    await callback.answer("Оновлено")

@router.callback_query(F.data == "change_location")
async def ask_for_location(callback: CallbackQuery):
    await callback.message.edit_text("🌍 Введіть назву вашого міста для прогнозу погоди:")

@router.message(F.text)
async def set_location(msg: Message):
    if msg.text.strip().lower() in ["налаштування", "/start"]:
        return
    user_id = msg.from_user.id
    settings = load_settings(user_id)
    settings["location"] = msg.text.strip()
    save_settings(user_id, settings)
    await msg.answer(f"✅ Місто оновлено на *{settings['location']}*", parse_mode="Markdown")
