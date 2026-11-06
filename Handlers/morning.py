from datetime import date, timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from database import get_user_profile
from day_storage import get_day_entry
from day_answers import snapshot_answers, medication_index
from Forms.day import DayEdit
from Handlers.routes import today_for_user
from Keyboards.day import completion_keyboard
from Keyboards.morning import morning_open_keyboard, morning_preview_keyboard
from localization import language_of, t
from morning_storage import (
    SLEEP_STEPS, finish_morning_session, first_other_step, get_morning_session,
    morning_date, next_morning_step, set_morning_step, start_morning_session,
    sleep_complete, other_complete,
)

router = Router()


async def morning_overview(message, user_id, sleep_date, lang, session=None):
    yesterday = sleep_date - timedelta(days=1)
    sleep = await get_day_entry(user_id, sleep_date) or {}
    other = await get_day_entry(user_id, yesterday) or {}
    # Этот краткий экран нужен только для заполненной записи или старого сценария.
    sleep_done, other_done = sleep_complete(sleep), other_complete(other)
    text = t(lang, "morning.short_dates", sleep_date=sleep_date, other_date=yesterday)
    if sleep_done and other_done:
        text += t(lang, "morning.already_complete")

    await message.answer(text, reply_markup=morning_preview_keyboard(
        sleep_date, lang, session, sleep_done=sleep_done, other_done=other_done))


async def finish_morning(message, state, session, lang):
    await finish_morning_session(session["user_id"], session["session_id"])
    await state.clear()
    sleep_date = date.fromisoformat(session["sleep_date"])
    other_date = date.fromisoformat(session["other_date"])
    await message.answer(t(lang, "morning.saved", sleep_date=sleep_date, other_date=other_date),
        reply_markup=completion_keyboard(sleep_date, lang=lang))


async def continue_morning(message, state, session, lang):
    step = await next_morning_step(session, session["step"])
    await set_morning_step(session["user_id"], session["session_id"], step)
    session["step"] = step
    if step == "complete":
        await finish_morning(message, state, session, lang)
        return
    draft = {
        "morning": True, "morning_id": session["session_id"],
        "edit_id": session["session_id"], "user_id": session["user_id"],
        "date": morning_date(session, step).isoformat(), "step": step,
    }
    previous = await state.get_data()
    if previous.get("morning_id") != session["session_id"]:
        dates = [date.fromisoformat(session["sleep_date"]), date.fromisoformat(session["other_date"])]
        snapshot = await snapshot_answers(session["user_id"], dates)
        draft["previous_values"] = snapshot
        draft["medicine_index"] = medication_index(snapshot, morning_date(session, step), step)
        await state.clear()
    elif previous.get("date") != draft["date"]:
        draft["medicine_index"] = medication_index(
            previous.get("previous_values", {}), morning_date(session, step), step)
    await state.set_state(DayEdit.answer)
    await state.update_data(**draft)
    draft = await state.get_data()
    from Handlers.day import send_question
    await send_question(message, state, draft, morning_date(session, step), step, lang=lang)


@router.callback_query(F.data.startswith("morning:"))
async def open_morning(callback: CallbackQuery, state):
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    profile = await get_user_profile(callback.from_user.id)
    lang = language_of(profile)
    if not profile or not profile["setup_complete"]:
        await callback.answer(t(lang, "privacy.start_required"), show_alert=True)
        return
    parts = callback.data.split(":")
    today = today_for_user(profile)
    session = await get_morning_session(callback.from_user.id)
    try:
        action = parts[1]
        if action == "resume" and len(parts) == 3:
            if not session or parts[2] != session["session_id"]:
                raise ValueError
            await callback.answer()
            await continue_morning(callback.message, state, session, lang)
            return
        sleep_date = date.fromisoformat(parts[2])
        if action not in ("open", "begin") or sleep_date > today:
            raise ValueError
        if sleep_date != today:
            await callback.answer()
            await callback.message.answer(t(lang, "morning.stale"),
                reply_markup=morning_open_keyboard(today, lang))
            if session:
                # Явные даты позволяют продолжить начатую запись после полуночи.
                await morning_overview(callback.message, callback.from_user.id,
                    date.fromisoformat(session["sleep_date"]), lang, session)
            return
        if action == "open" and len(parts) == 3:
            await callback.answer()
            sleep = await get_day_entry(callback.from_user.id, sleep_date)
            other = await get_day_entry(callback.from_user.id, sleep_date - timedelta(days=1))
            if sleep_complete(sleep) and other_complete(other):
                await morning_overview(callback.message, callback.from_user.id, sleep_date, lang, session)
                return
            # Открытие напоминания заполняет только пропуски, без экрана с пустыми полями.
            # Продолжение явной перезаписи доступно отдельно по кнопке resume.
            if (not session or session["sleep_date"] != sleep_date.isoformat()
                or session["edit_sleep"] or session["edit_other"]):
                session = await start_morning_session(
                    callback.from_user.id, sleep_date, "continue", profile["utc_offset"])
            await continue_morning(callback.message, state, session, lang)
            return
        if action != "begin" or len(parts) != 4 or parts[3] not in ("continue", "sleep", "other"):
            raise ValueError
        # Не затираем сохранённый сценарий простым повторным открытием.
        if (parts[3] == "continue" and session and session["sleep_date"] == sleep_date.isoformat()
            and not session["edit_sleep"] and not session["edit_other"]):
            await callback.answer()
            await continue_morning(callback.message, state, session, lang)
            return
        session = await start_morning_session(callback.from_user.id, sleep_date, parts[3], profile["utc_offset"])
        if parts[3] == "other":
            session["step"] = "mood_control"
            await set_morning_step(callback.from_user.id, session["session_id"], session["step"])
        await callback.answer()
        await continue_morning(callback.message, state, session, lang)
    except (ValueError, IndexError):
        await callback.answer(t(lang, "morning.expired"), show_alert=True)
