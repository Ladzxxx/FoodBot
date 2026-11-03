from aiogram.fsm.state import State, StatesGroup


class MealNote(StatesGroup):
    comment = State()
