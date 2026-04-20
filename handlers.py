from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from keyboards import main_kb, menu_kb
from states import RegisterState, LoginState, CapsuleState, DecryptState
from database import add_user, get_user, user_exists, save_message, get_available_capsules, mark_as_opened
from crypto import encrypt_message, decrypt_message
from datetime import datetime
import hashlib

router = Router()
user_sessions = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_handlers(dp):
    dp.include_router(router)

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Привет! Выберите действие:", reply_markup=main_kb)

# === Регистрация ===

@router.message(F.text == "📝 Зарегистрироваться")
async def register(msg: Message, state: FSMContext):
    await msg.answer("Введите имя пользователя:")
    await state.set_state(RegisterState.username)

@router.message(RegisterState.username)
async def reg_username(msg: Message, state: FSMContext):
    if user_exists(msg.text):
        await msg.answer("⚠️ Это имя уже занято. Пожалуйста, выберите другое.")
        return
    await state.update_data(username=msg.text)
    await msg.answer("Введите пароль:")
    await state.set_state(RegisterState.password)

@router.message(RegisterState.password)
async def reg_password(msg: Message, state: FSMContext):
    data = await state.get_data()
    add_user(data["username"], hash_password(msg.text))
    await msg.answer("✅ Регистрация завершена.", reply_markup=main_kb)
    await state.clear()

# === Вход ===

@router.message(F.text == "🔐 Войти")
async def login(msg: Message, state: FSMContext):
    await msg.answer("Введите имя пользователя:")
    await state.set_state(LoginState.username)

@router.message(LoginState.username)
async def login_username(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text)
    await msg.answer("Введите пароль:")
    await state.set_state(LoginState.password)

@router.message(LoginState.password)
async def login_password(msg: Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(data["username"], hash_password(msg.text))
    if user:
        user_sessions[msg.from_user.id] = data["username"]
        await msg.answer("✅ Успешный вход.")
        await msg.answer("Главное меню:", reply_markup=menu_kb)
    else:
        await msg.answer("❌ Неверные имя пользователя или пароль.")
    await state.clear()

# === Выход ===

@router.callback_query(F.data == "logout")
async def logout(callback: CallbackQuery, state: FSMContext):
    user_sessions.pop(callback.from_user.id, None)
    await state.clear()
    await callback.message.answer("🚪 Вы вышли из аккаунта.", reply_markup=main_kb)

# === Капсулы времени ===

@router.callback_query(F.data == "create_capsule")
async def start_capsule(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in user_sessions:
        await callback.message.answer("❌ Сначала войдите в аккаунт.")
        return
    await state.set_state(CapsuleState.message)
    await callback.message.answer("Введите сообщение для капсулы:")

@router.message(CapsuleState.message)
async def capsule_msg(msg: Message, state: FSMContext):
    await state.update_data(message=msg.text)
    await msg.answer("Введите ключ для шифрования:")
    await state.set_state(CapsuleState.key)

@router.message(CapsuleState.key)
async def capsule_key(msg: Message, state: FSMContext):
    await state.update_data(key=msg.text)
    await msg.answer("Введите имя получателя:")
    await state.set_state(CapsuleState.recipient)

@router.message(CapsuleState.recipient)
async def capsule_recipient(msg: Message, state: FSMContext):
    await state.update_data(recipient=msg.text)
    await msg.answer("Введите дату и время открытия (формат YYYY-MM-DD HH:MM):")
    await state.set_state(CapsuleState.time)

@router.message(CapsuleState.time)
async def capsule_time(msg: Message, state: FSMContext):
    try:
        datetime.strptime(msg.text, "%Y-%m-%d %H:%M")
    except ValueError:
        await msg.answer("❌ Неверный формат даты. Используйте YYYY-MM-DD HH:MM\nНапример: 2025-12-31 23:59")
        return
    data = await state.get_data()
    encrypted = encrypt_message(data["message"], data["key"])
    save_message(user_sessions[msg.from_user.id], data["recipient"], encrypted, msg.text)
    await msg.answer("📦 Капсула времени создана и будет доставлена в указанное время.")
    await state.clear()

# === Просмотр капсул ===

@router.callback_query(F.data == "view_capsules")
async def view_capsules(callback: CallbackQuery, state: FSMContext):
    user = user_sessions.get(callback.from_user.id)
    if not user:
        await callback.message.answer("❌ Сначала войдите в аккаунт.")
        return
    capsules = get_available_capsules(user)
    if not capsules:
        await callback.message.answer("📭 У вас нет капсул.")
        return
    for cap in capsules:
        if datetime.strptime(cap[4], "%Y-%m-%d %H:%M") <= datetime.now():
            await state.update_data(capsule_id=cap[0], encrypted=cap[3])
            await callback.message.answer(f"📬 Капсула от {cap[1]}!\nВведите ключ для расшифровки:")
            await state.set_state(DecryptState.key)
        else:
            await callback.message.answer(f"⌛ Капсула от {cap[1]} откроется {cap[4]}")

@router.message(DecryptState.key)
async def decrypt_capsule(msg: Message, state: FSMContext):
    data = await state.get_data()
    try:
        decrypted = decrypt_message(data["encrypted"], msg.text)
        await msg.answer(f"✉️ Сообщение из капсулы:\n\n{decrypted}")
        mark_as_opened(data["capsule_id"])
    except Exception:
        await msg.answer("❌ Неверный ключ. Попробуйте ещё раз:")
        return
    await state.clear()