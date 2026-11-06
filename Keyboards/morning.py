from datetime import timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization import t


def morning_open_keyboard(sleep_date, lang):
    # CAN CHANGE TEXT: кнопка содержит дату пробуждения, не дату вчерашней записи.
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "morning.open", date=sleep_date),
            callback_data=f"morning:open:{sleep_date.isoformat()}"),
    ]])


def morning_preview_keyboard(sleep_date, lang, session=None, *, sleep_done=False, other_done=False):
    day = sleep_date.isoformat()
    # CAN CHANGE TEXT: любое редактирование уже записанного блока — отдельное решение.
    rows = []
    if not (sleep_done and other_done):
        label = "morning.only_sleep" if other_done else "morning.continue_day"
        if not sleep_done and not other_done:
            label = "morning.continue"
        rows.append([InlineKeyboardButton(text=t(lang, label),
            callback_data=f"morning:begin:{day}:continue")])
    if session:
        rows.insert(0, [InlineKeyboardButton(text=t(lang, "morning.resume_dates", sleep_date=session["sleep_date"], other_date=session["other_date"]),
            callback_data=f"morning:resume:{session['session_id']}")])
    rows.extend([
        [InlineKeyboardButton(text=t(lang, "morning.edit_sleep"), callback_data=f"morning:begin:{day}:sleep")],
        [InlineKeyboardButton(text=t(lang, "morning.edit_other"), callback_data=f"morning:begin:{day}:other")],
        [InlineKeyboardButton(text=t(lang, "morning.view_other"), callback_data=f"painview:{(sleep_date - timedelta(days=1)).isoformat()}:0")],
    ])
    rows.append([InlineKeyboardButton(text=t(lang, "common.calendar"),
        callback_data=f"calendar:month:{sleep_date.replace(day=1).isoformat()}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
