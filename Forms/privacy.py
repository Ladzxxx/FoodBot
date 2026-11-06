from aiogram.fsm.state import State, StatesGroup


class PrivacySetup(StatesGroup):
    language = State()
    consent = State()
    delete = State()
