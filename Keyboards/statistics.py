from localization import t
from datetime import date, timedelta

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Keyboards.calendar import month_title


def month_statistics_keyboard(month_date: date, lang="en") -> InlineKeyboardMarkup:
    first = month_date.replace(day=1)
    rows = []
    # CAN CHANGE TEXT: кнопки статистики месяца.
    if first > date.min:
        previous = first - timedelta(days=1)
        rows.append([InlineKeyboardButton(
            text=month_title(previous.year, previous.month, lang=lang),
            callback_data=f"statistics:month:{previous.replace(day=1).isoformat()}",
        )])
    rows.append([InlineKeyboardButton(text=t(lang, 'statistics.meal_statistics'), callback_data="statistics:meals")])
    # CAN CHANGE TEXT
    rows.append([InlineKeyboardButton(text=t(lang, 'statistics.pain_statistics'), callback_data=f"painstats:{first.isoformat()}:0")])
    # CAN CHANGE TEXT
    rows.append([InlineKeyboardButton(text=t(lang, 'statistics.get_excel_file'), callback_data="statistics:excel")])
    rows.append([InlineKeyboardButton(text=t(lang, 'common.calendar'), callback_data=f"calendar:month:{first.isoformat()}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def statistics_menu_keyboard(months: list[str], page: int, today: date, lang="en") -> InlineKeyboardMarkup:
    rows = []
    # CAN CHANGE TEXT / LAYOUT: восемь месяцев на страницу, по два в строке.
    selected = months[page * 8:(page + 1) * 8]
    for index in range(0, len(selected), 2):
        buttons = []
        for month in selected[index:index + 2]:
            month_date = date.fromisoformat(month + "-01")
            # CAN CHANGE TEXT
            buttons.append(InlineKeyboardButton(
                text=f"📊 {month_title(month_date.year, month_date.month, lang=lang)}",
                callback_data=f"statistics:month:{month}-01",
            ))
        rows.append(buttons)
    navigation = []
    if page > 0:
        # CAN CHANGE TEXT
        navigation.append(InlineKeyboardButton(text=t(lang, 'statistics.months'), callback_data=f"statistics:all:{page - 1}"))
    if (page + 1) * 8 < len(months):
        # CAN CHANGE TEXT
        navigation.append(InlineKeyboardButton(text=t(lang, 'statistics.months_2'), callback_data=f"statistics:all:{page + 1}"))
    if navigation:
        rows.append(navigation)
    # CAN CHANGE TEXT
    rows.append([InlineKeyboardButton(text=t(lang, 'statistics.meal_statistics'), callback_data="statistics:meals")])
    # CAN CHANGE TEXT
    rows.append([InlineKeyboardButton(text=t(lang, 'statistics.pain_statistics'), callback_data="painstats:all:0")])
    # CAN CHANGE TEXT
    rows.append([InlineKeyboardButton(text=t(lang, 'statistics.get_excel_file'), callback_data="statistics:excel")])
    rows.append([InlineKeyboardButton(text=t(lang, 'common.calendar'), callback_data=f"calendar:month:{today.replace(day=1).isoformat()}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
