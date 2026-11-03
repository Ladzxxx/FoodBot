from localization import t
import calendar
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Forms.day import day_marker

# CAN CHANGE TEXT
# CAN CHANGE TEXT


def month_title(year: int, month: int, lang="en") -> str:
    return t(lang, "calendar.month_title", month=t(lang, f"calendar.month.{month}"), year=year)


def calendar_keyboard(
    month_date: date, entries: dict, today: date, selected_date: date | None = None,
    meal_page: int = 0, meal_pages: int = 1,
    meal_counts: dict | None = None,
    lang="en") -> InlineKeyboardMarkup:
    meal_counts = meal_counts or {}
    year = month_date.year
    month = month_date.month
    previous_year = year
    previous_month = month - 1
    if previous_month == 0:
        previous_year -= 1
        previous_month = 12

    next_year = year
    next_month = month + 1
    if next_month == 13:
        next_year += 1
        next_month = 1

    # У крайних лет Python не создаём кнопки с несуществующей датой.
    previous_callback = "calendar:ignore"
    if previous_year >= 1:
        previous_date = date(previous_year, previous_month, 1)
        previous_callback = f"calendar:month:{previous_date.isoformat()}"

    next_callback = "calendar:ignore"
    if (year, month) < (today.year, today.month) and next_year <= 9999:
        next_date = date(next_year, next_month, 1)
        next_callback = f"calendar:month:{next_date.isoformat()}"

    # CAN CHANGE TEXT
    rows = [[
        InlineKeyboardButton(text="←", callback_data=previous_callback),
        InlineKeyboardButton(text=month_title(year, month, lang=lang), callback_data="calendar:ignore"),
        InlineKeyboardButton(text="→", callback_data=next_callback),
    ]]
    # CAN CHANGE TEXT
    rows.append([
        InlineKeyboardButton(text=weekday, callback_data="calendar:ignore")
        for weekday in [t(lang, f"calendar.weekday.{i}") for i in range(7)]
    ])

    for week in calendar.monthcalendar(year, month):
        buttons = []
        has_days = False
        for day in week:
            if day == 0 or date(year, month, day) > today:
                # CAN CHANGE TEXT
                buttons.append(InlineKeyboardButton(text=" ", callback_data="calendar:ignore"))
                continue

            has_days = True
            day_date = date(year, month, day).isoformat()
            entry = entries.get(day_date, {})
            text = str(day)
            marker = day_marker(entry, meal_counts.get(day_date, 0))
            if marker:
                text += " " + marker

            # CAN CHANGE TEXT
            buttons.append(InlineKeyboardButton(
                text=text, callback_data=f"calendar:day:{day_date}"
            ))
        if has_days:
            rows.append(buttons)

    if selected_date is not None:
        day = selected_date.isoformat()
        # CAN CHANGE TEXT: листание еды в выбранном дне.
        meal_navigation = []
        if meal_page > 0:
            # CAN CHANGE TEXT
            meal_navigation.append(InlineKeyboardButton(text=t(lang, 'calendar.meals'), callback_data=f"calendar:meals:{day}:{meal_page - 1}"))
        if meal_page + 1 < meal_pages:
            # CAN CHANGE TEXT
            meal_navigation.append(InlineKeyboardButton(text=t(lang, 'calendar.meals_2'), callback_data=f"calendar:meals:{day}:{meal_page + 1}"))
        if meal_navigation:
            rows.append(meal_navigation)
        # CAN CHANGE TEXT
        rows.append([InlineKeyboardButton(text=t(lang, 'calendar.edit_the_day'), callback_data=f"day:edit:{day}")])
    month = month_date.replace(day=1).isoformat()
    # CAN CHANGE TEXT
    rows.append([InlineKeyboardButton(text=t(lang, 'common.statistics'), callback_data=f"statistics:month:{month}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
