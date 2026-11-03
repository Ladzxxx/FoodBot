from localization import t, language_of
from datetime import date, datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import get_user_profile
from day_storage import add_meal, update_meal_comment
from Forms.meal import MealNote
from Keyboards.meal import meal_comment_keyboard, meal_done_keyboard

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
    # CAN CHANGE TEXT: результат записи еды.
    description = comment or t(lang, 'common.no_comment')
    # CAN CHANGE TEXT
    text = t(lang, 'meal.meal_saved_selected_date_d_m_y_at_data', selected_date=selected_date, data=data['time'], description=description)
    await message.answer(text, reply_markup=meal_done_keyboard(selected_date, lang=lang))


@router.message(Command("meal"))
async def record_meal(message: Message, state: FSMContext, command: CommandObject):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    if message.from_user is None or message.chat.type != "private":
        return
    profile = language_profile
    if profile is None or not profile["setup_complete"]:
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'meal.please_finish_your_setup_with_start_first'))
        return
    await state.clear()
    now = datetime.now(timezone.utc)
    local_now = now.astimezone(timezone(timedelta(hours=profile["utc_offset"])))
    comment = meal_comment(command.args or "")
    valid_comment = comment if len(comment) <= 50 else ""
    meal_id = await add_meal(
        message.from_user.id, local_now.date(), local_now.strftime("%H:%M"),
        int(now.timestamp()), profile["utc_offset"], valid_comment,
    )
    data = {"meal_id": meal_id, "date": local_now.date().isoformat(), "time": local_now.strftime("%H:%M")}
    if valid_comment:
        await show_meal_saved(message, data, valid_comment, lang=lang)
        return
    # CAN CHANGE TEXT
    text = t(lang, "meal.prompt", time=data["time"], day=local_now.strftime("%d.%m.%Y"))
    if len(comment) > 50:
        # CAN CHANGE TEXT
        text += t(lang, 'meal.the_description_was_too_long_please_shorten_it_to')
    prompt = await message.answer(text, reply_markup=meal_comment_keyboard(meal_id, lang=lang))
    data["message_id"] = prompt.message_id
    await state.set_state(MealNote.comment)
    await state.set_data(data)


@router.message(MealNote.comment, F.text & ~F.text.startswith("/"))
async def describe_meal(message: Message, state: FSMContext):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    comment = meal_comment(message.text)
    if not 1 <= len(comment) <= 50:
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'meal.please_write_between_1_and_50_characters_or_tap'))
        return
    data = await state.get_data()
    await update_meal_comment(message.from_user.id, data["meal_id"], comment)
    await state.clear()
    await clear_meal_buttons(message, data["message_id"])
    await show_meal_saved(message, data, comment, lang=lang)


@router.callback_query(F.data.startswith("meal:skip:"))
async def skip_meal_comment(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    data = await state.get_data()
    if (
        await state.get_state() != MealNote.comment.state
        or callback.data != f"meal:skip:{data.get('meal_id')}"
        or not isinstance(callback.message, Message)
        or callback.message.message_id != data.get("message_id")
    ):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'meal.this_meal_is_already_recorded_open_callendar'), show_alert=True)
        return
    await state.clear()
    await callback.answer()
    await clear_meal_buttons(callback.message, data["message_id"])
    await show_meal_saved(callback.message, data, "", lang=lang)
