import re

from aiogram.fsm.state import State, StatesGroup


class MealNote(StatesGroup):
    comment = State()
    time = State()


def parse_meal_time(text):
    # Только ЧЧ:ММ, без переноса даты и значения 24:00.
    if not re.fullmatch(r"[0-9]{2}:[0-9]{2}", text):
        raise ValueError
    hour, minute = map(int, text.split(":"))
    if hour > 23 or minute > 59:
        raise ValueError
    return text


def parse_meal_input(text):
    text = text.strip()
    parts = text.split(maxsplit=1)
    first = parts[0] if parts else ""
    rest = parts[1] if len(parts) > 1 else ""
    if re.match(r"^[0-9]{1,2}:", first):
        return parse_meal_time(first), " ".join(rest.split())
    return None, " ".join(text.split())
