from localization import t
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# CAN CHANGE TEXT / OPTIONS: смещения и порядок UTC-кнопок.
UTC_OFFSETS = list(range(3, 13)) + list(range(-1, -12, -1)) + [0, 1, 2]


def commands_keyboard() -> ReplyKeyboardMarkup:
    # CAN CHANGE TEXT: постоянные команды под полем ввода Telegram.
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="/meal"),
            KeyboardButton(text="/callendar"),
            KeyboardButton(text="/settings"),
        ]],
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False,
    )


def profile_keyboard(field: str, profile: dict, lang="en") -> InlineKeyboardMarkup | None:
    if field == "language":
        # CAN CHANGE TEXT
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Русский", callback_data="profile:language:ru"),
            InlineKeyboardButton(text="English", callback_data="profile:language:en"),
        ]])
    if field == "gender":
        rows = []
        for gender in ("male", "female", "secret"):
            # CAN CHANGE TEXT
            rows.append([InlineKeyboardButton(text=t(lang, "profile.gender." + gender), callback_data=f"profile:gender:{gender}")])
        return InlineKeyboardMarkup(inline_keyboard=rows)
    if field == "utc_offset":
        rows = []
        for index in range(0, 24, 4):
            buttons = []
            for offset in UTC_OFFSETS[index:index + 4]:
                # CAN CHANGE TEXT
                text = t(lang, 'profile.offset_d_00_utc', offset=offset)
                if offset == 3:
                    # CAN CHANGE TEXT
                    text += t(lang, 'profile.moscow')
                # CAN CHANGE TEXT
                buttons.append(InlineKeyboardButton(text=text, callback_data=f"profile:utc_offset:{offset}"))
            rows.append(buttons)
        # CAN CHANGE TEXT
        rows.append([InlineKeyboardButton(text=t(lang, 'profile.moscow_3_00_utc'), callback_data="profile:utc_offset:3")])
        return InlineKeyboardMarkup(inline_keyboard=rows)
    if field == "reminder_period":
        # CAN CHANGE TEXT
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'profile.every_morning'), callback_data="profile:reminder_period:morning")],
            [InlineKeyboardButton(text=t(lang, 'profile.every_evening'), callback_data="profile:reminder_period:evening")],
        ])
    if field == "reminder_hour":
        first_hour = 6 if profile["reminder_period"] == "morning" else 18
        # CAN CHANGE TEXT
        clocks = ("🕕", "🕖", "🕗", "🕘", "🕙", "🕚")
        buttons = []
        for index, clock in enumerate(clocks):
            hour = first_hour + index
            # CAN CHANGE TEXT
            buttons.append(InlineKeyboardButton(text=f"{hour} {clock}", callback_data=f"profile:reminder_hour:{hour}"))
        # CAN CHANGE TEXT
        return InlineKeyboardMarkup(inline_keyboard=[
            buttons,
            [InlineKeyboardButton(text=t(lang, 'common.back'), callback_data="profile:back:reminder_period")],
        ])
    return None


def setup_complete_keyboard(selected_date: date, lang="en") -> InlineKeyboardMarkup:
    # CAN CHANGE TEXT
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, 'common.calendar'), callback_data=f"calendar:month:{selected_date.replace(day=1).isoformat()}")
    ]])
