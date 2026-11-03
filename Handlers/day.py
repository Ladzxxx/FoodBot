from localization import t, language_of
from datetime import date, datetime, timedelta, timezone
from secrets import token_hex

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import get_user_profile
from day_storage import add_medication, get_day_entry, get_meal_counts, get_medications, get_recent_entries, reset_day_draft, save_day_answer, save_medication_relief
from Forms.day import DayEdit, RATING_STEPS, TEXT_STEPS, TIME_STEPS, YES_NO_STEPS, day_marker, next_day_step, sleep_minutes
from Handlers.routes import day_text, replace_message, show_month, today_for_user
from Keyboards.day import completion_keyboard, diary_menu_keyboard, draft_choice_keyboard, question_keyboard
from Forms.pain import PAIN_QUESTIONS
from Handlers.pain import send_pain_question

router = Router()

# CAN CHANGE TEXT: английские дни недели и месяцы для списка последних записей.


def entry_day_label(selected_date: date, today: date, lang="en") -> str:
    # CAN CHANGE TEXT: названия дат на экране /makenote.
    days_ago = (today - selected_date).days
    if days_ago == 0:
        return t(lang, 'common.today')
    if days_ago == 1:
        return t(lang, 'common.yesterday')
    if 1 < days_ago < 7:
        return t(lang, f"calendar.weekday_full.{selected_date.weekday()}")
    label = t(lang, "day.history_date", month=t(lang, f"calendar.month_date.{selected_date.month}"), day=selected_date.day)
    if selected_date.year != today.year:
        label += f", {selected_date.year}"
    return label


def diary_menu_text(entries: list[dict], today: date, utc_offset: int, meal_counts: dict | None = None, lang="en") -> str:
    meal_counts = meal_counts or {}
    # CAN CHANGE TEXT: главный текст /makenote и формат списка последних записей.
    text = (
        t(lang, 'day.b_headache_diary_b_you_can_create_a_new')
    )
    if not entries:
        return text + t(lang, 'day.no_entries_yet')
    local_zone = timezone(timedelta(hours=utc_offset))
    for entry in entries:
        selected_date = date.fromisoformat(entry["entry_date"])
        if entry.get("updated_at") is None:
            # У прежних записей время неизвестно: не подставляем время миграции.
            clock = t(lang, 'day.time_not_recorded')
        else:
            saved_at = datetime.fromtimestamp(entry["updated_at"], local_zone)
            clock = f"{saved_at.hour % 12 or 12}:{saved_at.minute:02d} {t(lang, 'day.am') if saved_at.hour < 12 else t(lang, 'day.pm')}"
        marker = day_marker(entry, meal_counts.get(entry["entry_date"], 0))
        text += f"\n{entry_day_label(selected_date, today, lang=lang)}, {clock} — {marker}"
    return text


@router.message(Command("makenote"))
async def open_diary_menu(message: Message, state: FSMContext):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    if message.from_user is None or message.chat.type != "private":
        return
    profile = language_profile
    if profile is None or not profile["setup_complete"]:
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'day.please_finish_your_setup_with_start_first'))
        return
    await state.clear()
    today = today_for_user(profile)
    entries = await get_recent_entries(message.from_user.id, today)
    counts = await get_meal_counts(message.from_user.id, date.fromisoformat(entries[-1]["entry_date"]), today) if entries else {}
    await message.answer(diary_menu_text(entries, today, profile["utc_offset"], counts, lang=lang), reply_markup=diary_menu_keyboard(today, lang=lang), parse_mode="HTML")


def question_text(selected_date: date, step: str, lang="en") -> str:
    # CAN CHANGE TEXT
    text = t(lang, 'diary.editing_day', date=selected_date, question=t(lang, "day.question." + step))
    if step == "bedtime" and selected_date > date.min:
        # CAN CHANGE TEXT: явная дата помогает отличить вчерашний вечер от сегодняшнего.
        text += t(lang, 'day.bedtime_range_selected_date_d_m_y_12_00', selected_date=selected_date - timedelta(days=1), selected_date_value=selected_date)
    elif step == "wake_time":
        # CAN CHANGE TEXT
        text += t(lang, 'day.wake_up_date_selected_date_d_m_y', selected_date=selected_date)
    return text


def parse_time(text: str, lang="en") -> str:
    parts = text.strip().split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(t(lang, 'day.use_hh_mm'))
    if len(parts[0]) not in (1, 2) or len(parts[1]) != 2:
        raise ValueError(t(lang, 'day.use_hh_mm'))
    hour, minute = int(parts[0]), int(parts[1])
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError(t(lang, 'day.invalid_time'))
    return f"{hour:02d}:{minute:02d}"


def parse_button_answer(step: str, value: str, lang="en"):
    if step == "bedtime":
        return parse_bedtime(value, lang=lang)
    if step == "wake_time":
        if value.strip() == "24:00":
            return "24:00"
        return parse_time(value, lang=lang)
    if step in RATING_STEPS:
        rating = int(value)
        if 1 <= rating <= 10:
            return rating
    if step in YES_NO_STEPS and value in ("yes", "no"):
        return int(value == "yes")
    if step == "medicine_relief" and value in ("yes", "no", "a_little"):
        return value
    raise ValueError(t(lang, 'day.invalid_answer'))


def parse_bedtime(text: str, lang="en") -> tuple[str, int]:
    text = text.strip().lower()
    prefix, _, clock = text.partition(" ")
    prefix = {"вчера": "yesterday", "сегодня": "today"}.get(prefix, prefix)
    if prefix in ("yesterday", "today"):
        bedtime_day = -1 if prefix == "yesterday" else 0
        clock = parse_time(clock, lang=lang)
    else:
        clock = parse_time(text, lang=lang)
        bedtime_day = 0 if clock < "12:00" else -1
    if (bedtime_day == -1 and clock < "12:00") or (bedtime_day == 0 and clock > "12:00"):
        raise ValueError(t(lang, 'day.bedtime_is_outside_the_noon_to_noon_range'))
    return clock, bedtime_day


def recorded_answer_text(step: str, value, lang="en") -> str:
    if step == "bedtime":
        # CAN CHANGE TEXT: в подтверждении времени сохраняем выбранный день.
        clock, bedtime_day = value
        return f"{clock} ({t(lang, 'common.yesterday') if bedtime_day == -1 else t(lang, 'common.today')})"
    if step in YES_NO_STEPS:
        # CAN CHANGE TEXT
        return t(lang, 'common.yes') if value else t(lang, 'common.no')
    if step == "medicine_relief":
        # CAN CHANGE TEXT
        return {"yes": t(lang, 'common.yes'), "no": t(lang, 'common.no'), "a_little": t(lang, 'common.a_little')}[value]
    return str(value)


async def show_medications(message: Message, user_id: int, selected_date: date, lang="en"):
    medications = await get_medications(user_id, selected_date)
    # CAN CHANGE TEXT
    text = t(lang, 'day.all_recorded_medications')
    for index, medication in enumerate(medications, 1):
        relief = medication["relief"]
        # CAN CHANGE TEXT
        effect = recorded_answer_text("medicine_relief", relief, lang=lang) if relief else "___"
        # CAN CHANGE TEXT
        line = t(lang, 'day.index_medication_helped_effect', index=index, medication=medication['description'], effect=effect)
        if len(text) + len(line) > 3500:
            await message.answer(text)
            # CAN CHANGE TEXT
            text = t(lang, 'day.recorded_medications_continued')
        # CAN CHANGE TEXT
        text += "\n" + line
    await message.answer(text)


async def send_question(message: Message, state: FSMContext, draft: dict, selected_date: date, step: str, lang="en"):
    if step in PAIN_QUESTIONS:
        await send_pain_question(message, state, draft, selected_date, step, lang=lang)
        return
    # CAN CHANGE TEXT
    question = await message.answer(
        question_text(selected_date, step, lang=lang),
        reply_markup=question_keyboard(draft["edit_id"], step, selected_date, lang=lang),
    )
    await state.update_data(step=step, message_id=question.message_id)


async def record_answer(message: Message, user_id: int, state: FSMContext, value, lang="en"):
    draft = await state.get_data()
    selected_date = date.fromisoformat(draft["date"])
    step = draft["step"]
    entry = await get_day_entry(user_id, selected_date) or {}
    if entry and not entry["completed"] and entry["next_step"] != step:
        # Ответ мог сохраниться до сбоя Telegram. Повторно лекарство не добавляем.
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'day.your_previous_answer_is_already_saved_let_s_continue'))
        await send_question(message, state, draft, selected_date, entry["next_step"], lang=lang)
        return
    next_step = next_day_step(step, value, entry)
    if step == "wake_time":
        duration = sleep_minutes({**entry, "wake_time": value})
        if duration is not None and duration < 0:
            # CAN CHANGE TEXT: не сохраняем отрицательную длительность и повторяем вопрос.
            text = t(lang, 'day.sleep_time_cant_be_negative') + question_text(selected_date, step, lang=lang)
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id, message_id=draft["message_id"], text=text,
                    reply_markup=question_keyboard(draft["edit_id"], step, selected_date, lang=lang),
                )
            except TelegramBadRequest as error:
                if "message is not modified" not in error.message:
                    raise
            return
    if step == "bedtime":
        clock, bedtime_day = value
        await save_day_answer(user_id, selected_date, step, clock, next_step, bedtime_day=bedtime_day)
    elif step == "medicine_details":
        await add_medication(user_id, selected_date, value, replace_existing=entry.get("more_medicine") is None)
    elif step == "medicine_relief":
        await save_medication_relief(user_id, selected_date, value)
    else:
        await save_day_answer(user_id, selected_date, step, value, next_step)

    # Сначала сохраняем ответ, затем показываем его в исходном вопросе.
    # CAN CHANGE TEXT
    text = question_text(selected_date, step, lang=lang) + t(lang, 'day.answer_recorded') + recorded_answer_text(step, value, lang=lang)
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id, message_id=draft["message_id"], text=text, reply_markup=None
        )
    except TelegramBadRequest as error:
        if "message is not modified" not in error.message:
            raise
    if step == "more_medicine" and not value:
        await show_medications(message, user_id, selected_date, lang=lang)
    if step == "pain_description_requested" and value:
        await state.update_data(pain_confirmation_id=draft['message_id'])
        draft = await state.get_data()
    if next_step == "complete":
        await state.clear()
        entry = await get_day_entry(user_id, selected_date)
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'day.b_entry_saved_b') + day_text(selected_date, entry, lang=lang), reply_markup=completion_keyboard(selected_date, lang=lang), parse_mode="HTML")
        return
    await send_question(message, state, draft, selected_date, next_step, lang=lang)


async def requested_day(callback: CallbackQuery, date_text: str, lang="en", profile=None) -> date | None:
    if not isinstance(callback.message, Message):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'day.open_callendar'), show_alert=True)
        return
    try:
        selected_date = date.fromisoformat(date_text)
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'day.invalid_date_open_callendar'), show_alert=True)
        return
    if profile is None:
        profile = await get_user_profile(callback.from_user.id)
    if selected_date > today_for_user(profile):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'day.future_dates_are_not_available'), show_alert=True)
        return
    return selected_date


async def start_questions(callback: CallbackQuery, state: FSMContext, selected_date: date, step: str, lang="en"):
    edit_id = token_hex(6)
    await state.clear()
    if step in PAIN_QUESTIONS:
        await state.set_state(DayEdit.answer)
        draft = {"date": selected_date.isoformat(), "edit_id": edit_id, "step": step, "user_id": callback.from_user.id}
        await state.set_data(draft)
        await send_pain_question(callback.message, state, draft, selected_date, step, lang=lang)
        await callback.answer()
        return
    question = await replace_message(callback, question_text(selected_date, step, lang=lang), question_keyboard(edit_id, step, selected_date, lang=lang), lang=lang)
    if question is None:
        return
    await state.set_state(DayEdit.answer)
    await state.set_data({"date": selected_date.isoformat(), "edit_id": edit_id, "step": step, "message_id": question.message_id})


@router.callback_query(F.data.startswith("day:edit:"))
async def edit_day(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    selected_date = await requested_day(callback, callback.data.removeprefix("day:edit:"), lang=lang, profile=language_profile or {})
    if selected_date is None:
        return
    entry = await get_day_entry(callback.from_user.id, selected_date)
    if entry and not entry["completed"]:
        edit_id = token_hex(6)
        await state.clear()
        # CAN CHANGE TEXT: выбор способа открыть незавершённую запись.
        text = t(lang, 'day.you_have_an_unfinished_entry_for_selected_date_d', selected_date=selected_date)
        question = await replace_message(callback, text, draft_choice_keyboard(edit_id, selected_date, lang=lang), lang=lang)
        if question is not None:
            await state.set_state(DayEdit.choose)
            await state.set_data({"date": selected_date.isoformat(), "edit_id": edit_id, "message_id": question.message_id})
        return
    await start_questions(callback, state, selected_date, "bedtime", lang=lang)


@router.callback_query(F.data.startswith("day:draft:"))
async def choose_draft(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    data = await state.get_data()
    try:
        _, _, edit_id, action = callback.data.split(":")
        if (
            await state.get_state() != DayEdit.choose.state or edit_id != data.get("edit_id")
            or action not in ("resume", "clean") or not isinstance(callback.message, Message)
            or callback.message.message_id != data.get("message_id")
        ):
            raise ValueError
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'day.this_draft_choice_has_expired_open_callendar'), show_alert=True)
        return
    selected_date = await requested_day(callback, data["date"], lang=lang, profile=language_profile or {})
    if selected_date is None:
        return
    entry = await get_day_entry(callback.from_user.id, selected_date)
    if entry is None or entry["completed"]:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'day.this_draft_has_changed_open_callendar'), show_alert=True)
        return
    if action == "clean":
        if not await reset_day_draft(callback.from_user.id, selected_date):
            # CAN CHANGE TEXT
            await callback.answer(t(lang, 'day.this_draft_has_changed_open_callendar'), show_alert=True)
            return
        step = "bedtime"
    else:
        step = entry["next_step"]
    await start_questions(callback, state, selected_date, step, lang=lang)


@router.callback_query(F.data.startswith("day:answer:"))
async def answer_button(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    draft = await state.get_data()
    try:
        _, _, edit_id, step, raw_value = callback.data.split(":", 4)
        if (
            await state.get_state() != DayEdit.answer.state
            or edit_id != draft.get("edit_id") or step != draft.get("step")
            or not isinstance(callback.message, Message)
            or callback.message.message_id != draft.get("message_id")
        ):
            raise ValueError
        value = parse_button_answer(step, raw_value, lang=lang)
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'day.this_answer_is_invalid_or_the_question_has_expired'), show_alert=True)
        return
    await callback.answer()
    await record_answer(callback.message, callback.from_user.id, state, value, lang=lang)


@router.message(DayEdit.answer, F.text & ~F.text.startswith("/"))
async def answer_text(message: Message, state: FSMContext):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    draft = await state.get_data()
    step = draft["step"]
    try:
        if step in TIME_STEPS:
            value = parse_button_answer(step, message.text, lang=lang)
        elif step in TEXT_STEPS:
            value = message.text.strip()
            limit = 300 if step == "medicine_details" else 1000
            # CAN CHANGE TEXT / LIMIT: общая заметка дня — до 200 символов.
            if step == "day_comment":
                limit = 200
            if not 1 <= len(value) <= limit:
                raise ValueError
        else:
            # CAN CHANGE TEXT
            await message.answer(t(lang, 'day.please_use_the_buttons_for_this_question'))
            return
    except ValueError:
        # CAN CHANGE TEXT
        error = t(lang, 'day.please_enter_a_valid_time_as_hh_mm') if step in TIME_STEPS else t(lang, 'day.please_write_between_1_and_limit_characters', limit=limit)
        await message.answer(error)
        return
    await record_answer(message, message.from_user.id, state, value, lang=lang)


@router.callback_query(F.data.startswith("day:cancel:"))
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    try:
        _, _, date_text, edit_id = callback.data.split(":")
        selected_date = date.fromisoformat(date_text)
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'day.invalid_date_open_callendar'), show_alert=True)
        return
    draft = await state.get_data()
    if draft and (draft.get("edit_id") != edit_id or not isinstance(callback.message, Message) or draft.get("message_id") != callback.message.message_id):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'day.this_edit_has_expired_open_callendar'), show_alert=True)
        return
    await state.clear()
    await show_month(callback, selected_date, lang=lang, profile=language_profile or {})


@router.callback_query(F.data.startswith("day:rate:"))
async def old_rating_button(callback: CallbackQuery):
    # CAN CHANGE TEXT
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    await callback.answer(t(lang, 'day.the_diary_questions_have_changed_open_callendar'), show_alert=True)
