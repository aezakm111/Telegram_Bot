from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from keyboards import main_kb, menu_kb
from states import RegisterState, LoginState, CapsuleState, DecryptState
from database import (add_user, get_user, user_exists, save_message,
                      get_available_capsules, mark_as_opened,
                      update_chat_id, get_opened_capsules)
from crypto import encrypt_message, decrypt_message
from datetime import datetime
import hashlib
import logging

router = Router()
user_sessions = {}
logger = logging.getLogger(__name__)

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
    username = msg.text.strip().lstrip("@")
    if user_exists(username):
        await msg.answer("⚠️ Это имя уже занято. Пожалуйста, выберите другое.")
        return
    await state.update_data(username=username)
    await msg.answer("Введите пароль:")
    await state.set_state(RegisterState.password)

@router.message(RegisterState.password)
async def reg_password(msg: Message, state: FSMContext):
    data = await state.get_data()
    add_user(data["username"], hash_password(msg.text), msg.chat.id)
    user_sessions[msg.from_user.id] = data["username"]
    await msg.answer("✅ Регистрация завершена! Вы автоматически вошли в аккаунт.")
    await msg.answer("Главное меню:", reply_markup=menu_kb)
    await state.clear()

# === Вход ===

@router.message(F.text == "🔐 Войти")
async def login(msg: Message, state: FSMContext):
    await msg.answer("Введите имя пользователя:")
    await state.set_state(LoginState.username)

@router.message(LoginState.username)
async def login_username(msg: Message, state: FSMContext):
    username = msg.text.strip().lstrip("@")
    await state.update_data(username=username)
    await msg.answer("Введите пароль:")
    await state.set_state(LoginState.password)

@router.message(LoginState.password)
async def login_password(msg: Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(data["username"], hash_password(msg.text))
    if user:
        user_sessions[msg.from_user.id] = data["username"]
        update_chat_id(data["username"], msg.chat.id)
        await msg.answer("✅ Успешный вход.")
        await msg.answer("Главное меню:", reply_markup=menu_kb)
        logger.info(f"Пользователь {data['username']} вошёл в аккаунт")
    else:
        await msg.answer("❌ Неверные имя пользователя или пароль.")
    await state.clear()

# === Выход ===

@router.message(F.text == "🚪 Выйти")
async def logout(msg: Message, state: FSMContext):
    username = user_sessions.pop(msg.from_user.id, None)
    await state.clear()
    await msg.answer("🚪 Вы вышли из аккаунта.", reply_markup=main_kb)
    logger.info(f"Пользователь {username} вышел из аккаунта")

# === Создать капсулу ===

@router.message(F.text == "✉️ Создать капсулу")
async def start_capsule(msg: Message, state: FSMContext):
    if msg.from_user.id not in user_sessions:
        await msg.answer("❌ Сначала войдите в аккаунт.", reply_markup=main_kb)
        return
    await msg.answer("Введите сообщение для капсулы:")
    await state.set_state(CapsuleState.message)

@router.message(CapsuleState.message)
async def capsule_msg(msg: Message, state: FSMContext):
    await state.update_data(message=msg.text)
    await msg.answer("🔐 Введите ключ для шифрования:\n⚠️ Получатель должен знать этот ключ чтобы расшифровать сообщение!")
    await state.set_state(CapsuleState.key)

@router.message(CapsuleState.key)
async def capsule_key(msg: Message, state: FSMContext):
    await state.update_data(key=msg.text)
    await msg.answer("👤 Введите имя получателя:\nМожно с @ или без, например: @nargiz1 или nargiz1")
    await state.set_state(CapsuleState.recipient)

@router.message(CapsuleState.recipient)
async def capsule_recipient(msg: Message, state: FSMContext):
    recipient = msg.text.strip().lstrip("@")
    if not user_exists(recipient):
        await msg.answer("❌ Пользователь не найден. Проверьте имя и попробуйте снова:")
        return
    await state.update_data(recipient=recipient)
    await msg.answer("📅 Введите дату и время открытия:\nФормат: YYYY-MM-DD HH:MM\nНапример: 2026-12-31 23:59")
    await state.set_state(CapsuleState.time)

@router.message(CapsuleState.time)
async def capsule_time(msg: Message, state: FSMContext):
    try:
        open_time = datetime.strptime(msg.text.strip(), "%Y-%m-%d %H:%M")
        if open_time <= datetime.now():
            await msg.answer("❌ Дата должна быть в будущем. Попробуйте снова:")
            return
    except ValueError:
        await msg.answer("❌ Неверный формат. Используйте YYYY-MM-DD HH:MM\nНапример: 2026-12-31 23:59")
        return
    data = await state.get_data()
    encrypted = encrypt_message(data["message"], data["key"])
    save_message(user_sessions[msg.from_user.id], data["recipient"], encrypted, msg.text.strip())
    await msg.answer(f"📦 Капсула создана! Получатель {data['recipient']} получит её {msg.text.strip()}")
    logger.info(f"Капсула создана от {user_sessions[msg.from_user.id]} для {data['recipient']}")
    await state.clear()

# === Мои капсулы ===

@router.message(F.text == "📬 Мои капсулы")
async def view_capsules(msg: Message, state: FSMContext):
    user = user_sessions.get(msg.from_user.id)
    if not user:
        await msg.answer("❌ Сначала войдите в аккаунт.", reply_markup=main_kb)
        return
    capsules = get_available_capsules(user)
    if not capsules:
        await msg.answer("📭 У вас нет новых капсул.")
        return
    for cap in capsules:
        if datetime.strptime(cap[4], "%Y-%m-%d %H:%M") <= datetime.now():
            await state.update_data(capsule_id=cap[0], encrypted=cap[3], sender=cap[1])
            await msg.answer(f"📬 Капсула от {cap[1]}!\n🔐 Введите ключ для расшифровки:")
            await state.set_state(DecryptState.key)
        else:
            await msg.answer(f"⌛ Капсула от {cap[1]} откроется {cap[4]}")

@router.message(DecryptState.key)
async def decrypt_capsule(msg: Message, state: FSMContext):
    data = await state.get_data()
    try:
        decrypted = decrypt_message(data["encrypted"], msg.text)
        await msg.answer(f"✉️ Сообщение от {data['sender']}:\n\n{decrypted}")
        mark_as_opened(data["capsule_id"])
        logger.info(f"Капсула {data['capsule_id']} расшифрована")
    except Exception:
        await msg.answer("❌ Неверный ключ. Попробуйте ещё раз:")
        return
    await state.clear()

# === История капсул ===

@router.message(F.text == "📜 История капсул")
async def capsule_history(msg: Message):
    user = user_sessions.get(msg.from_user.id)
    if not user:
        await msg.answer("❌ Сначала войдите в аккаунт.", reply_markup=main_kb)
        return
    capsules = get_opened_capsules(user)
    if not capsules:
        await msg.answer("📭 История капсул пуста.")
        return
    await msg.answer("📜 Ваши открытые капсулы:")
    for cap in capsules:
        await msg.answer(f"📬 От: {cap[1]}\n📅 Открыта: {cap[4]}")