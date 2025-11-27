from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔐 Войти")],
        [KeyboardButton(text="📝 Зарегистрироваться")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Создать капсулу времени", callback_data="create_capsule")],
        [InlineKeyboardButton(text="📬 Мои полученные капсулы", callback_data="view_capsules")],
        [InlineKeyboardButton(text="🚪 Выйти", callback_data="logout")]
    ]
)
