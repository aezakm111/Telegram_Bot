from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔐 Войти")],
        [KeyboardButton(text="📝 Зарегистрироваться")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✉️ Создать капсулу")],
        [KeyboardButton(text="📬 Мои капсулы"), KeyboardButton(text="📜 История капсул")],
        [KeyboardButton(text="🚪 Выйти")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)