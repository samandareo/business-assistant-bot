from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    message_text_id = State()
    message_text = State()

class AdminState(StatesGroup):
    message_text = State()