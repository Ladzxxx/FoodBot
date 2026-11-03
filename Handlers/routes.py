from localization import t, language_of
import calendar
from datetime import date, datetime, timedelta, timezone
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from database import get_user_profile
from day_storage import get_meal_counts, get_meals, get_month_entries
from Handlers.commands import show_reply_menu
from Keyboards.calendar import calendar_keyboard, month_title

router = Router()


def rating_text(value: int | None, lang="en") -> str:
    if value is None:
        # CAN CHANGE TEXT
        return "___"
    # CAN CHANGE TEXT
    return f"{value}/10   |{'⭐️' * value}"


def day_text(selected_date: date, entry: dict, lang="en") -> str:
    bedtime = entry.get("bedtime") or "___"
    if entry.get("bedtime") and entry.get("bedtime_day") == 0:
        # CAN CHANGE TEXT: отличаем отход ко сну в выбранный день от предыдущего вечера.
        bedtime += t(lang, 'routes.today')
    wake_time = entry.get("wake_time") or "___"
    ache = entry.get("ache")
    # CAN CHANGE TEXT
    ache_text = "___" if ache is None else (t(lang, 'common.yes') if ache else t(lang, 'common.no'))
    # CAN CHANGE TEXT
    return (
        t(lang, 'calendar.day_summary', date=selected_date, bedtime=bedtime, wake_time=wake_time, sleep_satisfaction=rating_text(entry.get('sleep_satisfaction'), lang=lang), mood=rating_text(entry.get('mood_control'), lang=lang), ache_text=ache_text)
    )


def calendar_text(month_date: date, entry: dict, selected_date: date | None = None, meals: list | None = None, meal_page: int = 0, lang="en") -> str:
    # CAN CHANGE TEXT
    text = f"<b>{month_title(month_date.year, month_date.month, lang=lang)}</b>\n\n"
    if selected_date is None:
        # CAN CHANGE TEXT
        text += t(lang, 'routes.select_a_day_to_view_its_entry')
    else:
        text += day_text(selected_date, entry, lang=lang)
        # CAN CHANGE TEXT: строки еды в выбранной дате.
        text += t(lang, 'routes.b_meals_b')
        if not meals:
            # CAN CHANGE TEXT
            text += t(lang, 'routes.no_meals_recorded')
        else:
            for index, meal in enumerate(meals[meal_page * 10:(meal_page + 1) * 10], meal_page * 10 + 1):
                # CAN CHANGE TEXT
                # Пользовательский комментарий экранируем, чтобы он не стал HTML-разметкой.
                text += t(lang, 'routes.meal_index_meal_escape', index=index, meal=meal['meal_time'], escape=escape(meal['comment'] or t(lang, 'common.no_comment')))
            if len(meals) > 10:
                # CAN CHANGE TEXT
                text += t(lang, 'routes.meals_page_meal_page_meals', meal_page=meal_page + 1, meals=(len(meals) + 9) // 10)
        # CAN CHANGE TEXT / LIMIT: старые длинные заметки в базе сохраняются целиком.
        comment = (entry.get("day_comment") or "")[:200]
        text += t(lang, 'routes.b_day_comment_b') + escape(comment or "___")
    return text


async def update_message(
    callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup, lang="en"
):
    if not isinstance(callback.message, Message):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'routes.open_the_calendar_with_callendar'), show_alert=True)
        return

    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except TelegramBadRequest as error:
        # Повторное быстрое нажатие может оставить текст и кнопки прежними.
        if "message is not modified" not in error.message:
            raise
    await callback.answer()


async def delete_screen_message(message: Message, lang="en"):
    try:
        await message.delete()
    except TelegramBadRequest as error:
        if "message to delete not found" in error.message:
            return True
        if "message can't be deleted" not in error.message:
            raise
        return False
    return True


async def replace_message(
    callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup , lang="en") -> Message | None:
    if not isinstance(callback.message, Message):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'routes.open_the_calendar_with_callendar'), show_alert=True)
        return None

    await callback.answer()
    deleted = await delete_screen_message(callback.message, lang=lang)
    if deleted:
        return await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    # Если Telegram запрещает удаление, обновляем старый экран без второго календаря.
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    return callback.message


async def calendar_screen(user_id: int, month_date: date, selected_date: date | None = None, meal_page: int = 0, lang="en", profile=None):
    if profile is None:
        profile = await get_user_profile(user_id)
    today = today_for_user(profile)
    if month_date.replace(day=1) > today.replace(day=1):
        month_date = today
        selected_date = None
    if selected_date is not None and selected_date > today:
        selected_date = None
    entries = await get_month_entries(user_id, month_date.year, month_date.month)
    first = month_date.replace(day=1)
    last = month_date.replace(day=calendar.monthrange(month_date.year, month_date.month)[1])
    meal_counts = await get_meal_counts(user_id, first, last)
    entry = entries.get(selected_date.isoformat(), {}) if selected_date is not None else {}
    meals = await get_meals(user_id, selected_date) if selected_date is not None else []
    meal_pages = max(1, (len(meals) + 9) // 10)
    meal_page = max(0, min(meal_page, meal_pages - 1))
    text = calendar_text(month_date, entry, selected_date, meals, meal_page, lang=lang)
    return text, calendar_keyboard(month_date, entries, today, selected_date, meal_page, meal_pages, meal_counts, lang=lang)


async def show_month(callback: CallbackQuery, month_date: date, selected_date: date | None = None, lang="en", profile=None):
    text, keyboard = await calendar_screen(callback.from_user.id, month_date, selected_date, lang=lang, profile=profile)
    await replace_message(callback, text, keyboard, lang=lang)


def today_for_user(profile: dict | None) -> date:
    if profile is None or profile.get("utc_offset") is None:
        return date.today()
    user_timezone = timezone(timedelta(hours=profile["utc_offset"]))
    return datetime.now(user_timezone).date()


@router.message(Command("callendar"))
async def open_calendar(message: Message, state: FSMContext, profile=None):
    language_profile = profile if profile is not None else (await get_user_profile(message.from_user.id) if message.from_user else None)
    lang = language_of(language_profile)
    if message.from_user is None:
        return

    profile = language_profile
    if profile is None or not profile["setup_complete"]:
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'routes.please_finish_your_setup_with_start_first'))
        return
    await state.clear()
    await show_reply_menu(message, lang=lang)
    text, keyboard = await calendar_screen(message.from_user.id, today_for_user(profile), lang=lang, profile=profile)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "calendar:ignore")
async def ignore_button(callback: CallbackQuery):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    await callback.answer()


@router.callback_query(F.data.startswith("calendar:month:"))
@router.callback_query(F.data.startswith("calendar:day:"))
async def open_date(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    try:
        selected_date = date.fromisoformat(callback.data.split(":", 2)[2])
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'routes.invalid_date_open_callendar'), show_alert=True)
        return

    today = today_for_user(language_profile)
    is_day = callback.data.startswith("calendar:day:")
    if selected_date.replace(day=1) > today.replace(day=1) or (is_day and selected_date > today):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'routes.future_dates_are_not_available'), show_alert=True)
        return
    await state.clear()
    await show_month(callback, selected_date, selected_date if is_day else None, lang=lang, profile=language_profile or {})


@router.callback_query(F.data.startswith("calendar:answer:"))
async def old_answer_button(callback: CallbackQuery):
    # Кнопки «Да/Нет» из ранее отправленных сообщений больше ничего не записывают.
    # CAN CHANGE TEXT
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    await callback.answer(t(lang, 'routes.this_button_is_no_longer_used_open_callendar'), show_alert=True)


@router.callback_query(F.data.startswith("calendar:meals:"))
async def show_meals_page(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    try:
        _, _, date_text, page_text = callback.data.split(":")
        selected_date = date.fromisoformat(date_text)
        page = int(page_text)
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'routes.invalid_meal_page_open_callendar'), show_alert=True)
        return
    today = today_for_user(language_profile)
    if selected_date > today:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'routes.future_dates_are_not_available'), show_alert=True)
        return
    await state.clear()
    text, keyboard = await calendar_screen(callback.from_user.id, selected_date, selected_date, page, lang=lang, profile=language_profile or {})
    await replace_message(callback, text, keyboard, lang=lang)
