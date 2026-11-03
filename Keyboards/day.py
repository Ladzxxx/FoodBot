from localization import t
from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Forms.day import RATING_STEPS, TIME_STEPS, YES_NO_STEPS


def question_keyboard(edit_id: str, step: str, selected_date: date, lang="en") -> InlineKeyboardMarkup:
    rows = []
    choices = []
    width = 5
    if step in RATING_STEPS:
        choices = [(str(value), str(value)) for value in range(1, 11)]
    elif step == "bedtime":
        previous_date = selected_date - timedelta(days=1) if selected_date > date.min else selected_date
        # CAN CHANGE TEXT: две части диапазона явно показывают день отхода ко сну.
        for label, day_date, hours, prefix in (
            (t(lang, 'common.yesterday'), previous_date, range(12, 24), "yesterday"),
            (t(lang, 'common.today'), selected_date, range(13), "today"),
        ):
            rows.append([InlineKeyboardButton(text=f"{label} ({day_date:%d.%m.%Y})", callback_data="calendar:ignore")])
            for first_hour in range(hours.start, hours.stop, 4):
                rows.append([
                    InlineKeyboardButton(text=f"{hour:02d}:00", callback_data=f"day:answer:{edit_id}:{step}:{prefix} {hour:02d}:00")
                    for hour in range(first_hour, min(first_hour + 4, hours.stop))
                ])
    elif step in TIME_STEPS:
        # CAN CHANGE TEXT
        choices = [(f"{hour:02d}:00", f"{hour:02d}:00") for hour in range(25)]
        width = 4
    elif step in YES_NO_STEPS:
        # CAN CHANGE TEXT
        choices = [(t(lang, 'common.yes'), "yes"), (t(lang, 'common.no'), "no")]
    elif step == "medicine_relief":
        # CAN CHANGE TEXT
        choices = [(t(lang, 'common.yes'), "yes"), (t(lang, 'common.no'), "no"), (t(lang, 'common.a_little'), "a_little")]
    for index in range(0, len(choices), width):
        # CAN CHANGE TEXT
        rows.append([
            InlineKeyboardButton(text=text, callback_data=f"day:answer:{edit_id}:{step}:{value}")
            for text, value in choices[index:index + width]
        ])
    day = selected_date.isoformat()
    # CAN CHANGE TEXT
    rows.append([InlineKeyboardButton(text=t(lang, 'common.cancel'), callback_data=f"day:cancel:{day}:{edit_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def completion_keyboard(selected_date: date, lang="en") -> InlineKeyboardMarkup:
    month = selected_date.replace(day=1).isoformat()
    # CAN CHANGE TEXT
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, 'common.calendar'), callback_data=f"calendar:month:{month}")],
        [InlineKeyboardButton(text=t(lang, 'common.statistics'), callback_data=f"statistics:month:{month}")],
    ])


def reminder_keyboard(selected_date: date, lang="en") -> InlineKeyboardMarkup:
    # CAN CHANGE TEXT
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t(lang, 'day.make_a_note_about_selected_date_d_m_y', selected_date=selected_date),
            callback_data=f"day:edit:{selected_date.isoformat()}",
        )
    ]])


def draft_choice_keyboard(edit_id: str, selected_date: date, lang="en") -> InlineKeyboardMarkup:
    # CAN CHANGE TEXT: выбор между сохранённым черновиком и чистой записью.
    month = selected_date.replace(day=1).isoformat()
    # CAN CHANGE TEXT
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, 'day.continue_draft'), callback_data=f"day:draft:{edit_id}:resume")],
        [InlineKeyboardButton(text=t(lang, 'day.start_clean'), callback_data=f"day:draft:{edit_id}:clean")],
        [InlineKeyboardButton(text=t(lang, 'common.calendar'), callback_data=f"calendar:month:{month}")],
    ])


def diary_menu_keyboard(today: date, lang="en") -> InlineKeyboardMarkup:
    yesterday = today - timedelta(days=1)
    # CAN CHANGE TEXT: кнопки /makenote используют те же обработчики записи дня.
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, 'day.make_note_for_today_today_d_m_y', today=today), callback_data=f"day:edit:{today.isoformat()}")],
        [InlineKeyboardButton(text=t(lang, 'day.make_note_for_yesterday_yesterday_d_m_y', yesterday=yesterday), callback_data=f"day:edit:{yesterday.isoformat()}")],
        [InlineKeyboardButton(text=t(lang, 'day.view_the_calendar'), callback_data=f"calendar:month:{today.replace(day=1).isoformat()}")],
    ])
