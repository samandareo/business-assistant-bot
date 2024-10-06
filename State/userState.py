from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    message_text_id = State()
    message_text = State()

class AdminState(StatesGroup):
    message_text = State()

class AdminStateOne(StatesGroup):
    userOneId = State()
    message_text = State()

class UserMessagesToAdmin(StatesGroup):
    message_text = State()
    message_proove = State()

class CreatePoll(StatesGroup):
    message_text = State()
    message_proove = State()