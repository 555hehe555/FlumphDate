from aiogram import F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from utils import load_json, save_settings, is_time_in_range, get_weekday_name, get_weather
from datetime import datetime

# Дані
LESSONS = load_json('lessons.json')
HOLIDAYS = load_json('holidays.json')
settings = load_json('user_settings.json')

# Клавіатура головного меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📅 Розклад на сьогодні'), KeyboardButton(text='📆 Час уроків')],
        [KeyboardButton(text='🎉 Свята'), KeyboardButton(text='⚙️ Налаштування')],
        [KeyboardButton(text='🧹 Очистити чат')],
    ],
    resize_keyboard=True
)

# Типові налаштування користувача
def default_user_conf():
    return {
        'morning_digest': True,
        'morning_time': '06:00',
        'notify_start': True,
        'notify_end': True,
        'sound': True
    }

# Генерація інлайн-клавіатури налаштувань
def get_settings_kb(conf):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"Ранкова розсилка ({conf['morning_time']}): {'✅' if conf['morning_digest'] else '❌'}",
                callback_data='toggle_morning'
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Повідомлення старту уроку: {'✅' if conf['notify_start'] else '❌'}",
                callback_data='toggle_start'
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Повідомлення кінця уроку: {'✅' if conf['notify_end'] else '❌'}",
                callback_data='toggle_end'
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Звук: {'🔊' if conf['sound'] else '🔇'}",
                callback_data='toggle_sound'
            )
        ]
    ])

# Реєстрація хендлерів
def register_handlers(dp, bot, settings):
    dp.message.register(start_cmd, Command('start'))
    dp.message.register(text_menu, F.text == '⚙️ Налаштування')
    dp.callback_query.register(toggle_setting)
    dp.message.register(today_schedule, F.text == '📅 Розклад на сьогодні')
    dp.message.register(full_schedule, F.text == '📆 Час уроків')
    dp.message.register(today_holidays, F.text == '🎉 Свята')
    dp.message.register(clear_chat, F.text == '🧹 Очистити чат')

# /start
async def start_cmd(message: Message):
    await message.answer("Привіт! Я бот-датник 🤖", reply_markup=main_kb)

# Меню налаштувань
async def text_menu(message: Message):
    uid = str(message.from_user.id)
    conf = settings.get(uid, default_user_conf())
    await message.answer("Налаштування:", reply_markup=get_settings_kb(conf))

# Перемикання налаштувань
async def toggle_setting(query: CallbackQuery):
    uid = str(query.from_user.id)
    conf = settings.get(uid, default_user_conf())

    if query.data == 'toggle_morning':
        conf['morning_digest'] = not conf['morning_digest']
    elif query.data == 'toggle_start':
        conf['notify_start'] = not conf['notify_start']
    elif query.data == 'toggle_end':
        conf['notify_end'] = not conf['notify_end']
    elif query.data == 'toggle_sound':
        conf['sound'] = not conf['sound']

    settings[uid] = conf
    save_settings(settings)
    await query.answer("Оновлено")
    await query.message.edit_reply_markup(reply_markup=get_settings_kb(conf))

# Розклад на сьогодні
async def today_schedule(message: Message):
    day = get_weekday_name()
    lessons = LESSONS['lessons'].get(day, [])
    if lessons:
        text = f"<b>{day}</b>\n" + '\n'.join(f"{i+1}. {l}" for i, l in enumerate(lessons))
    else:
        text = f"<b>{day}</b>\nВихідний 😎"
    await message.answer(text)

# Час уроків
async def full_schedule(message: Message):
    now = datetime.now().time()
    lines = []
    for i, interval in enumerate(LESSONS['time_lessons']):
        mark = ' 🟢' if is_time_in_range(interval, now) else ''
        lines.append(f"{i+1}. {interval}{mark}")
    await message.answer("<b>Час уроків</b>\n" + '\n'.join(lines))

# Свята
async def today_holidays(message: Message):
    today = datetime.now().strftime('%m-%d')
    hol = HOLIDAYS.get(today, [])
    if hol:
        text = '<b>Свята сьогодні:</b>\n' + '\n'.join(f"{h}" for h in hol)
    else:
        text = 'Сьогодні немає свят!'
    await message.answer(text)

# Очищення чату
async def clear_chat(message: Message):
    chat_id = message.chat.id
    last_msg_id = message.message_id
    await message.answer("Очищаю чат...")
    for _ in range(100):
        try:
            await message.bot.delete_message(chat_id, last_msg_id)
        except:
            pass
        last_msg_id -= 1
    await message.answer("Чат очищено!", reply_markup=main_kb)
