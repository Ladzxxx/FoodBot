from localization import t
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def meal_comment_keyboard(meal_id: int, lang="en") -> InlineKeyboardMarkup:
    # CAN CHANGE TEXT: кнопка пропуска описания еды.
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, 'common.skip'), callback_data=f"meal:skip:{meal_id}")
    ]])


def meal_done_keyboard(selected_date: date, lang="en") -> InlineKeyboardMarkup:
    # CAN CHANGE TEXT: возврат после записи еды.
    month = selected_date.replace(day=1).isoformat()
    # CAN CHANGE TEXT
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, 'common.calendar'), callback_data=f"calendar:month:{month}")
    ]])
