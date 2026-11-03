from localization import t, language_of
import calendar
import asyncio
from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from database import get_user_profile
from day_storage import get_all_entries, get_legacy_entries, get_meals, get_month_entries
from day_storage import get_export_data
from day_export import make_excel_file
from Forms.day import has_green_marker, sleep_minutes
from Handlers.routes import today_for_user, update_message
from Keyboards.calendar import month_title
from Keyboards.statistics import month_statistics_keyboard, statistics_menu_keyboard

router = Router()


@router.callback_query(F.data == "statistics:excel")
async def export_excel(callback: CallbackQuery):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    if not isinstance(callback.message, Message) or callback.message.chat.type != "private" or callback.message.chat.id != callback.from_user.id:
        await callback.answer()
        return
    # CAN CHANGE TEXT
    await callback.answer(t(lang, 'statistics.preparing_your_excel_file'))
    data = await get_export_data(callback.from_user.id)
    # Создание XLSX не блокирует обработку сообщений других пользователей.
    content = await asyncio.to_thread(make_excel_file, data, lang=lang)
    if content is None:
        # CAN CHANGE TEXT
        await callback.message.answer(t(lang, 'statistics.no_saved_notes_yet_make_a_note_with_makenote'))
        return
    # Файл существует только в памяти и отправляется в личный чат владельца.
    await callback.message.answer_document(
        BufferedInputFile(content, filename=t(lang, "export.filename")),
        caption=t(lang, "export.caption"),
    )


def pain_statistics_pages(entries, answers, options, lang="en"):
    from Forms.pain import PAIN_OPTIONS, PAIN_QUESTIONS
    from Handlers.pain import text_pages
    pain_days = {day for day, entry in entries.items() if entry.get('ache') == 1}
    values = [entries[day]['pain_intensity'] for day in pain_days if entries[day].get('pain_intensity') is not None]
    # CAN CHANGE TEXT: интенсивность отдельно, без подстановки нулей.
    intensity = f'{sum(values) / len(values):.2f}/10 (N = {len(values)})' if values else t(lang, 'statistics.no_data_yet_n_0')
    header = t(lang, 'statistics.days_with_stomach_pain_pain_days_average_pain_intensity', pain_days=len(pain_days), intensity=intensity)
    pages = []
    for key in PAIN_QUESTIONS:
        group = [item for item in answers if item['question_key'] == key and item['entry_date'] in pain_days and entries[item['entry_date']].get('pain_description_requested') == 1]
        valid_dates = {item['entry_date'] for item in group if item['status'] in ('answered', 'none')}
        answered_dates = {item['entry_date'] for item in group if item['status'] == 'answered'}
        selected = [item for item in options if item['question_key'] == key and item['entry_date'] in answered_dates and item['is_selected']]
        # CAN CHANGE TEXT
        title = t(lang, 'statistics.user_suspected_triggers') if key == 'pain_triggers' else t(lang, "pain.question." + key).split('\n')[0]
        text = header + title + t(lang, 'statistics.n_valid_dates_confirmed_dates', valid_dates=len(valid_dates))
        for status, label in (('unknown', t(lang, 'common.not_sure')), ('skipped', t(lang, 'statistics.skipped')), ('in_progress', t(lang, 'statistics.in_progress'))):
            text += f"{label}: {sum(item['status'] == status for item in group)}\n"
        text += t(lang, 'statistics.no_answer_pain_days', pain_days=len(pain_days - {item['entry_date'] for item in group}))
        if not valid_dates:
            text += t(lang, 'statistics.no_data_yet')
        else:
            for code, original_label in PAIN_OPTIONS[key]:
                label = t(lang, "pain.option." + key + "." + code)
                count = len({item['entry_date'] for item in selected if item['option_code'] == code})
                text += f'\n{label}: {count} ({count / len(valid_dates) * 100:.1f}%)'
        # CAN CHANGE TEXT
        text += t(lang, 'statistics.multiple_selections_are_allowed_percentages_may_total_more_than')
        pages.append(text)
        custom = [f"{item['entry_date']}: {item['custom_text']}" for item in selected if item['option_code'] == 'other' and item['custom_text']]
        if custom:
            pages.extend(text_pages(title + t(lang, 'statistics.other_original_user_text') + '\n'.join(custom)))
    return pages


@router.callback_query(F.data.startswith('painstats:'))
async def pain_statistics(callback: CallbackQuery):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    from pain_storage import get_pain_answers
    from Handlers.pain import page_keyboard
    if not isinstance(callback.message, Message) or callback.message.chat.type != 'private':
        await callback.answer()
        return
    try:
        _, period, raw_page = callback.data.split(':')
        page = int(raw_page)
        if period == 'all':
            first, last = date.min, date.max
            title = t(lang, 'statistics.all_time')
        else:
            first = date.fromisoformat(period).replace(day=1)
            last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
            title = month_title(first.year, first.month, lang=lang)
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'statistics.invalid_period'), show_alert=True)
        return
    entries = await get_all_entries(callback.from_user.id)
    entries = {day: entry for day, entry in entries.items() if first.isoformat() <= day <= last.isoformat()}
    answers, options = await get_pain_answers(callback.from_user.id, first, last)
    pages = pain_statistics_pages(entries, answers, options, lang=lang)
    page = max(0, min(page, len(pages) - 1))
    today = today_for_user(language_profile)
    back = today if period == 'all' else first
    # CAN CHANGE TEXT
    await callback.message.edit_text(t(lang, 'statistics.pain_statistics_title_page_page_pages', title=title, page=page + 1, pages=len(pages)) + pages[page],
        reply_markup=page_keyboard(f'painstats:{period}', page, len(pages), f'calendar:month:{back.replace(day=1).isoformat()}', lang=lang))
    await callback.answer()


def average_rating(entries: dict, name: str, lang="en") -> str:
    values = []
    for entry in entries.values():
        if entry.get(name) is not None:
            values.append(entry[name])
    if not values:
        # CAN CHANGE TEXT: пропущенные оценки не считаются низкими.
        return t(lang, 'statistics.no_data_yet_0_below_7')
    below = sum(value < 7 for value in values)
    # CAN CHANGE TEXT: средняя оценка и число оценок строго ниже 7.
    return t(lang, 'statistics.values_2f_10_below_below_7', values=sum(values) / len(values), below=below)


def summary_text(entries: dict, meals: list, legacy: list, lang="en") -> str:
    durations = []
    pain_days = 0
    green_days = 0
    dates = set(entries)
    meal_counts = {}
    for meal in meals:
        day = meal["entry_date"]
        dates.add(day)
        meal_counts[day] = meal_counts.get(day, 0) + 1
    for day, entry in entries.items():
        pain_days += int(entry.get("ache") == 1)
        green_days += int(has_green_marker(entry, meal_counts.get(day, 0)))
        duration = sleep_minutes(entry)
        if duration is not None and duration >= 0:
            durations.append(duration)
    for old in legacy:
        dates.add(old["entry_date"])
    if durations:
        duration = round(sum(durations) / len(durations))
        sleep = t(lang, 'statistics.duration_h_duration_value_02d_min', duration=duration // 60, duration_value=duration % 60)
    else:
        sleep = t(lang, 'common.no_data')
    # CAN CHANGE TEXT: состав и подписи статистики.
    text = (
        t(lang, 'statistics.summary', days=len(dates), sleep=sleep, satisfaction=average_rating(entries, 'sleep_satisfaction', lang=lang), mood=average_rating(entries, 'mood_control', lang=lang), pain_days=pain_days, green_days=green_days, meals=len(meals))
    )
    return text


def statistics_text(month_date: date, entries: dict, meals: list | None = None, legacy: list | None = None, lang="en") -> str:
    # CAN CHANGE TEXT
    return t(lang, 'statistics.b_statistics_month_title_b', month_title=month_title(month_date.year, month_date.month, lang=lang)) + summary_text(entries, meals or [], legacy or [], lang=lang)


async def all_statistics_screen(user_id: int, page: int = 0, lang="en", profile=None):
    if profile is None:
        profile = await get_user_profile(user_id)
    today = today_for_user(profile)
    # CAN CHANGE TEXT / PERIOD: здесь выбран предыдущий календарный месяц.
    previous = today.replace(day=1) - timedelta(days=1)
    prefix = previous.isoformat()[:7]
    entries = await get_all_entries(user_id)
    meals = await get_meals(user_id)
    legacy = await get_legacy_entries(user_id)
    recent_entries = {day: entry for day, entry in entries.items() if day.startswith(prefix)}
    recent_meals = [meal for meal in meals if meal["entry_date"].startswith(prefix)]
    recent_legacy = [old for old in legacy if old["entry_date"].startswith(prefix)]
    # CAN CHANGE TEXT: заголовки общих итогов и предыдущего календарного месяца.
    text = t(lang, 'statistics.b_all_time_statistics_b') + summary_text(entries, meals, legacy, lang=lang)
    # CAN CHANGE TEXT
    text += t(lang, 'statistics.b_previous_month_month_title_b', month_title=month_title(previous.year, previous.month, lang=lang))
    text += summary_text(recent_entries, recent_meals, recent_legacy, lang=lang)
    months = {day[:7] for day in entries}
    months.update(meal["entry_date"][:7] for meal in meals)
    months.update(old["entry_date"][:7] for old in legacy)
    months = sorted((month for month in months if month <= today.isoformat()[:7]), reverse=True)
    page = max(0, min(page, max(0, (len(months) - 1) // 8)))
    return text, statistics_menu_keyboard(months, page, today, lang=lang)


@router.message(Command("statistics"))
async def statistics_command(message: Message, state: FSMContext):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    if message.from_user is None:
        return
    await state.clear()
    text, keyboard = await all_statistics_screen(message.from_user.id, lang=lang, profile=language_profile or {})
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "statistics:meals")
async def meal_statistics_placeholder(callback: CallbackQuery):
    # Кнопка пока только завершает индикатор нажатия и ничего не меняет.
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    await callback.answer()


@router.callback_query(F.data.startswith("statistics:all:"))
async def all_statistics_page(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    try:
        page = int(callback.data.removeprefix("statistics:all:"))
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'statistics.invalid_statistics_page_use_statistics'), show_alert=True)
        return
    await state.clear()
    text, keyboard = await all_statistics_screen(callback.from_user.id, page, lang=lang, profile=language_profile or {})
    await update_message(callback, text, keyboard, lang=lang)


@router.callback_query(F.data.startswith("statistics:month:"))
async def open_statistics(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    try:
        month_date = date.fromisoformat(callback.data.removeprefix("statistics:month:"))
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'statistics.invalid_date_open_callendar'), show_alert=True)
        return
    today = today_for_user(language_profile)
    if month_date.replace(day=1) > today.replace(day=1):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'statistics.future_dates_are_not_available'), show_alert=True)
        return
    await state.clear()
    first = month_date.replace(day=1)
    last = month_date.replace(day=calendar.monthrange(month_date.year, month_date.month)[1])
    entries = await get_month_entries(callback.from_user.id, month_date.year, month_date.month)
    meals = await get_meals(callback.from_user.id, first, last)
    legacy = await get_legacy_entries(callback.from_user.id)
    prefix = first.isoformat()[:7]
    legacy = [old for old in legacy if old["entry_date"].startswith(prefix)]
    await update_message(callback, statistics_text(month_date, entries, meals, legacy, lang=lang), month_statistics_keyboard(month_date, lang=lang), lang=lang)
