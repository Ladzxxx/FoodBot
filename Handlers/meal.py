from localization import t, language_of
from datetime import date, datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import get_user_profile
from day_storage import add_meal, get_meal, update_meal_comment, update_meal_time
from Forms.meal import MealNote, parse_meal_input, parse_meal_time
from Keyboards.meal import meal_comment_keyboard, meal_done_keyboard, meal_time_keyboard

router = Router()


def meal_comment(text: str) -> str:
    # CAN CHANGE TEXT / FORMAT: в календаре описание еды занимает одну строку.
    return " ".join(text.split())


async def clear_meal_buttons(message: Message, message_id: int):
    try:
        await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)
    except TelegramBadRequest as error:
        if "message is not modified" not in error.message and "message to edit not found" not in error.message:
            raise


async def show_meal_saved(message: Message, data: dict, comment: str, lang="en"):
    selected_date = date.fromisoformat(data["date"])
    # CAN CHANGE TEXT
    text = t(lang, 'meal.meal_saved_selected_date_d_m_y_at_data',
        selected_date=selected_date, data=data["time"], description=comment or t(lang, "common.no_comment"))
    if data.get("previous_time") is not None:
        text = t(lang, "meal.time_changed", old=data["previous_time"], new=data["time"]) + text
    await message.answer(text, reply_markup=meal_done_keyboard(
        selected_date, lang=lang, meal_id=data["meal_id"]))


async def show_meal_prompt(message, state, data, lang, too_long=False):
    # CAN CHANGE TEXT
    selected_date = date.fromisoformat(data["date"])
    text = t(lang, "meal.prompt", time=data["time"], day=selected_date.strftime("%d.%m.%Y"))
    text += t(lang, "meal.time_hint")
    if too_long:
        text += t(lang, "meal.the_description_was_too_long_please_shorten_it_to")
    prompt = await message.answer(text, reply_markup=meal_comment_keyboard(data["meal_id"], lang=lang))
    await state.set_state(MealNote.comment)
    await state.set_data({**data, "message_id": prompt.message_id})


@router.message(Command("meal"))
async def record_meal(message: Message, state: FSMContext, command: CommandObject):
    profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(profile)
    if message.from_user is None or message.chat.type != "private":
        return
    if profile is None or not profile["setup_complete"]:
        await message.answer(t(lang, "meal.please_finish_your_setup_with_start_first"))
        return
    try:
        chosen_time, comment = parse_meal_input(command.args or "")
    except ValueError:
        await message.answer(t(lang, "meal.invalid_time"))
        return
    await state.clear()
    now = datetime.now(timezone.utc)
    local_now = now.astimezone(timezone(timedelta(hours=profile["utc_offset"])))
    clock = chosen_time or local_now.strftime("%H:%M")
    valid_comment = comment if len(comment) <= 50 else ""
    meal_id = await add_meal(message.from_user.id, local_now.date(), clock,
        int(now.timestamp()), profile["utc_offset"], valid_comment)
    data = {"meal_id": meal_id, "date": local_now.date().isoformat(), "time": clock}
    if valid_comment:
        await show_meal_saved(message, data, valid_comment, lang=lang)
        return
    await show_meal_prompt(message, state, data, lang, too_long=len(comment) > 50)


@router.message(MealNote.comment, F.text & ~F.text.startswith("/"))
async def describe_meal(message: Message, state: FSMContext):
    lang = language_of(await get_user_profile(message.from_user.id))
    data = await state.get_data()
    try:
        clock, comment = parse_meal_input(message.text)
    except ValueError:
        await message.answer(t(lang, "meal.invalid_time"))
        return
    if len(comment) > 50 or (not comment and clock is None):
        await message.answer(t(lang, "meal.please_write_between_1_and_50_characters_or_tap"))
        return
    if clock is not None:
        if not await update_meal_time(message.from_user.id, data["meal_id"], clock):
            await state.clear()
            await message.answer(t(lang, "meal.not_found"))
            return
        data["previous_time"], data["time"] = data["time"], clock
    if not comment:
        # Введённое время меняет ту же запись, а не добавляет ещё один приём пищи.
        await clear_meal_buttons(message, data["message_id"])
        await show_meal_prompt(message, state, data, lang)
        return
    await update_meal_comment(message.from_user.id, data["meal_id"], comment)
    await state.clear()
    await clear_meal_buttons(message, data["message_id"])
    await show_meal_saved(message, data, comment, lang=lang)


@router.callback_query(F.data.startswith("meal:skip:"))
async def skip_meal_comment(callback: CallbackQuery, state: FSMContext):
    lang = language_of(await get_user_profile(callback.from_user.id))
    data = await state.get_data()
    if (await state.get_state() != MealNote.comment.state
        or callback.data != f"meal:skip:{data.get('meal_id')}"
        or not isinstance(callback.message, Message)
        or callback.message.message_id != data.get("message_id")):
        await callback.answer(t(lang, "meal.this_meal_is_already_recorded_open_callendar"), show_alert=True)
        return
    await state.clear()
    await callback.answer()
    await clear_meal_buttons(callback.message, data["message_id"])
    await show_meal_saved(callback.message, data, "", lang=lang)


@router.callback_query(F.data.startswith("meal:time:"))
async def choose_meal_time(callback: CallbackQuery, state: FSMContext):
    lang = language_of(await get_user_profile(callback.from_user.id))
    try:
        meal_id = int(callback.data.removeprefix("meal:time:"))
    except ValueError:
        await callback.answer(t(lang, "meal.not_found"), show_alert=True)
        return
    meal = await get_meal(callback.from_user.id, meal_id)
    if meal is None or not isinstance(callback.message, Message):
        await callback.answer(t(lang, "meal.not_found"), show_alert=True)
        return
    previous = await state.get_data()
    return_to_comment = (await state.get_state() == MealNote.comment.state
        and previous.get("meal_id") == meal_id)
    await callback.answer()
    await clear_meal_buttons(callback.message, callback.message.message_id)
    await state.clear()
    prompt = await callback.message.answer(t(lang, "meal.time_question",
        date=date.fromisoformat(meal["entry_date"]), time=meal["meal_time"]),
        reply_markup=meal_time_keyboard(meal_id, lang))
    await state.set_state(MealNote.time)
    await state.set_data({
        "meal_id": meal_id, "date": meal["entry_date"], "time": meal["meal_time"],
        "comment": meal["comment"], "message_id": prompt.message_id,
        "return_to_comment": return_to_comment,
    })


async def finish_time_edit(message, state, data, lang):
    await state.clear()
    await clear_meal_buttons(message, data["message_id"])
    if data["return_to_comment"]:
        await show_meal_prompt(message, state, data, lang)
    else:
        await show_meal_saved(message, data, data["comment"], lang=lang)


@router.message(MealNote.time, F.text & ~F.text.startswith("/"))
async def save_meal_time(message: Message, state: FSMContext):
    lang = language_of(await get_user_profile(message.from_user.id))
    data = await state.get_data()
    try:
        clock = parse_meal_time(message.text.strip())
    except ValueError:
        await message.answer(t(lang, "meal.invalid_time"))
        return
    if not await update_meal_time(message.from_user.id, data["meal_id"], clock):
        await state.clear()
        await message.answer(t(lang, "meal.not_found"))
        return
    data["previous_time"], data["time"] = data["time"], clock
    await finish_time_edit(message, state, data, lang)


@router.callback_query(F.data.startswith("meal:time_cancel:"))
async def cancel_meal_time(callback: CallbackQuery, state: FSMContext):
    lang = language_of(await get_user_profile(callback.from_user.id))
    data = await state.get_data()
    if (await state.get_state() != MealNote.time.state
        or callback.data != f"meal:time_cancel:{data.get('meal_id')}"
        or not isinstance(callback.message, Message)
        or callback.message.message_id != data.get("message_id")):
        await callback.answer(t(lang, "meal.not_found"), show_alert=True)
        return
    await callback.answer()
    await finish_time_edit(callback.message, state, data, lang)
