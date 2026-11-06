from localization import t
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def meal_comment_keyboard(meal_id: int, lang="en") -> InlineKeyboardMarkup:
    # CAN CHANGE TEXT: кнопка пропуска описания еды.
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "meal.change_time"), callback_data=f"meal:time:{meal_id}")],
        [InlineKeyboardButton(text=t(lang, 'common.skip'), callback_data=f"meal:skip:{meal_id}")],
    ])


def meal_done_keyboard(selected_date: date, lang="en", meal_id=None) -> InlineKeyboardMarkup:
    # CAN CHANGE TEXT: возврат после записи еды.
    month = selected_date.replace(day=1).isoformat()
    # CAN CHANGE TEXT
    rows = []
    if meal_id is not None:
        rows.append([InlineKeyboardButton(text=t(lang, "meal.change_time"), callback_data=f"meal:time:{meal_id}")])
    rows.append([InlineKeyboardButton(text=t(lang, 'common.calendar'), callback_data=f"calendar:month:{month}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def meal_time_keyboard(meal_id, lang):
    # CAN CHANGE TEXT
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "common.cancel"), callback_data=f"meal:time_cancel:{meal_id}")
    ]])
