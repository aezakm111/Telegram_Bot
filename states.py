from aiogram.fsm.state import StatesGroup, State

class RegisterState(StatesGroup):
    username = State()
    password = State()

class LoginState(StatesGroup):
    username = State()
    password = State()

class CapsuleState(StatesGroup):
    message = State()
    key = State()
    recipient = State()
    time = State()


class DecryptState(StatesGroup):
    key = State()
