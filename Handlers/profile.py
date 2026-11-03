from localization import t, language_of, first_language
from datetime import date
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, InlineKeyboardButton, InlineKeyboardMarkup

from database import (
    ensure_user_profile, get_user_profile, reset_reminder_choice,
    save_profile_answer, save_profile_settings, update_user_timezone,
)
from Forms.profile import PROFILE_IMAGES, PROFILE_IMAGES_RU, PROFILE_QUESTIONS, ProfileEdit, next_profile_field
from Handlers.commands import show_reply_menu, set_chat_commands
from Handlers.routes import open_calendar, today_for_user
from Keyboards.profile import UTC_OFFSETS, commands_keyboard, profile_keyboard, setup_complete_keyboard

router = Router()
IMAGES_DIR = Path(__file__).resolve().parent.parent / "Images"


def profile_image(field: str, lang="en") -> FSInputFile:
    filename = PROFILE_IMAGES[field]
    if lang == "ru":
        filename = PROFILE_IMAGES_RU.get(field, filename)
    # Путь не зависит от папки, из которой запущен main.py.
    return FSInputFile(IMAGES_DIR / filename)


async def show_profile_question(message: Message, profile: dict, welcome: bool = False, lang="en"):
    field = next_profile_field(profile)
    text = t(lang, "profile.question." + field)
    if welcome:
        # Приветствие идёт первым и устанавливает постоянное меню; вопрос языка — следом.
        await message.answer_photo(profile_image("welcome", lang), caption=t(lang, "profile.welcome"), reply_markup=commands_keyboard())
    keyboard = profile_keyboard(field, profile, lang=lang)
    if field in PROFILE_IMAGES:
        await message.answer_photo(profile_image(field, lang), caption=text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


def profile_answer_text(field: str, value, lang="en") -> str:
    # CAN CHANGE TEXT: подписи записанных ответов; значения в базе остаются прежними.
    if field == "language":
        return {"en": t(lang, 'profile.english'), "ru": t(lang, 'profile.russian')}[value]
    if field == "gender":
        # Сохранено для возврата отключённого вопроса в PROFILE_QUESTIONS.
        return t(lang, "profile.gender." + value)
    if field == "utc_offset":
        return t(lang, 'profile.value_d_00_utc', value=value)
    if field == "reminder_period":
        return {"morning": t(lang, 'profile.every_morning'), "evening": t(lang, 'profile.every_evening')}[value]
    if field == "reminder_hour":
        return f"{value % 12 or 12}:00 {t(lang, 'profile.am') if value < 12 else t(lang, 'profile.pm')}"
    return str(value)


async def show_profile_answer(message: Message, field: str, value, lang="en"):
    # CAN CHANGE TEXT: отдельное подтверждение перед следующим вопросом настройки.
    await message.answer(t(lang, 'profile.wrote_the_answer') + profile_answer_text(field, value, lang=lang))


async def current_answers(user_id: int, state: FSMContext, profile=None):
    editing = await state.get_state() == ProfileEdit.settings.state
    if editing:
        data = await state.get_data()
        return dict(data["profile_answers"]), True
    return profile, False


def validate_button(field: str, value: str, profile: dict, lang="en"):
    if field == "language" and value in ("en", "ru"):
        return value
    if field == "gender" and value in ("male", "female", "secret"):
        # Не вызывается, пока поле отключено в PROFILE_QUESTIONS.
        return value
    if field == "reminder_period" and value in ("morning", "evening"):
        return value
    if field == "utc_offset" and int(value) in UTC_OFFSETS:
        return int(value)
    if field == "reminder_hour":
        hours = range(6, 12) if profile["reminder_period"] == "morning" else range(18, 24)
        if int(value) in hours:
            return int(value)
    raise ValueError(t(lang, 'profile.invalid_profile_answer'))


async def store_answer(user_id: int, state: FSMContext, profile: dict, editing: bool, field: str, value):
    if not editing:
        await save_profile_answer(user_id, field, value)
        return await get_user_profile(user_id)
    profile[field] = value
    if field == "reminder_hour":
        await save_profile_settings(user_id, profile)
        await state.clear()
        return await get_user_profile(user_id)
    await state.update_data(profile_answers=profile)
    return profile


async def show_setup_complete(message: Message, profile: dict, lang="en"):
    await set_chat_commands(message.bot, message.chat.id, lang)
    hour = profile["reminder_hour"]
    suffix = t(lang, 'profile.am') if hour < 12 else t(lang, 'profile.pm')
    # CAN CHANGE TEXT: подтверждение настройки времени.
    text = (
        t(lang, 'profile.excellent_i_ll_remind_you_of_my_presence_after', hour=hour % 12 or 12, suffix=suffix)
    )
    await message.answer_photo(profile_image("complete", lang), caption=text, reply_markup=setup_complete_keyboard(today_for_user(profile), lang=lang))


@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    language_draft = await state.get_data()
    lang = language_draft.get("profile_answers", {}).get("language") or lang
    if message.from_user is None:
        return
    if message.chat.type != "private":
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'profile.please_open_a_private_chat_with_me_and_send'))
        return
    await state.clear()
    await ensure_user_profile(message.from_user.id, message.chat.id)
    profile = language_profile or await get_user_profile(message.from_user.id)
    lang = profile.get("language") or first_language(message.from_user)
    if profile["setup_complete"]:
        await set_chat_commands(message.bot, message.chat.id, lang)
        await open_calendar(message, state, profile=profile)
        return
    if profile["language"] is not None:
        await show_reply_menu(message, lang=lang)
    await show_profile_question(message, profile, welcome=profile["language"] is None, lang=lang)


@router.message(Command("settings"))
async def edit_settings(message: Message, state: FSMContext):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    language_draft = await state.get_data()
    lang = language_draft.get("profile_answers", {}).get("language") or lang
    if message.from_user is None or message.chat.type != "private":
        return
    profile = language_profile
    if profile is None or not profile["setup_complete"]:
        await start(message, state)
        return
    await state.clear()
    answers = {field: None for field in PROFILE_QUESTIONS}
    await state.set_state(ProfileEdit.settings)
    await state.set_data({"profile_answers": answers})
    # CAN CHANGE TEXT: старые настройки действуют до завершения редактирования.
    await message.answer(t(lang, 'profile.let_s_update_your_settings_your_current_settings_stay'), reply_markup=commands_keyboard())
    await show_profile_question(message, answers, lang=lang)


@router.message(Command("timezone"))
async def edit_timezone(message: Message, state: FSMContext):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    language_draft = await state.get_data()
    lang = language_draft.get("profile_answers", {}).get("language") or lang
    if message.from_user is None or message.chat.type != "private":
        return
    profile = language_profile
    if profile is None or not profile["setup_complete"]:
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'profile.please_finish_your_setup_with_start_first'))
        return
    await state.clear()
    await state.set_state(ProfileEdit.timezone)
    # CAN CHANGE TEXT
    await message.answer_photo(profile_image("utc_offset", lang), caption=t(lang, "profile.question.utc_offset"), reply_markup=profile_keyboard("utc_offset", profile, lang=lang))


@router.callback_query(ProfileEdit.timezone, F.data.startswith("profile:"))
async def answer_timezone(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    language_draft = await state.get_data()
    lang = language_draft.get("profile_answers", {}).get("language") or lang
    try:
        _, field, raw_value = callback.data.split(":", 2)
        if field != "utc_offset" or not isinstance(callback.message, Message):
            raise ValueError
        offset = validate_button(field, raw_value, {}, lang=lang)
    except ValueError:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'profile.please_choose_a_time_zone_using_the_buttons'), show_alert=True)
        return
    await update_user_timezone(callback.from_user.id, offset)
    language_profile["utc_offset"] = offset
    await state.clear()
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    profile = language_profile
    # CAN CHANGE TEXT: результат быстрого изменения UTC-смещения.
    text = t(lang, 'profile.time_zone_saved_offset_d_00_utc_your_reminder', offset=offset)
    await callback.message.answer(text, reply_markup=setup_complete_keyboard(today_for_user(profile), lang=lang))


@router.callback_query(F.data.startswith("profile:"))
async def answer_profile_button(callback: CallbackQuery, state: FSMContext):
    language_profile = await get_user_profile(callback.from_user.id) if callback.from_user else None
    lang = language_of(language_profile)
    language_draft = await state.get_data()
    lang = language_draft.get("profile_answers", {}).get("language") or lang
    if not isinstance(callback.message, Message):
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'profile.please_send_start_in_a_private_chat'), show_alert=True)
        return
    profile, editing = await current_answers(callback.from_user.id, state, profile=language_profile)
    if profile is None:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'profile.please_send_start_first'), show_alert=True)
        return
    if not editing and profile["setup_complete"]:
        # CAN CHANGE TEXT
        await callback.answer(t(lang, 'profile.your_setup_is_already_complete_open_settings_to_change'), show_alert=True)
        return
    field = next_profile_field(profile)
    if callback.data == "profile:back:reminder_period" and field == "reminder_hour":
        if editing:
            profile["reminder_period"] = None
            profile["reminder_hour"] = None
            await state.update_data(profile_answers=profile)
        else:
            await reset_reminder_choice(callback.from_user.id)
            profile = await get_user_profile(callback.from_user.id)
    else:
        try:
            _, button_field, raw_value = callback.data.split(":", 2)
            if button_field != field:
                raise ValueError
            value = validate_button(field, raw_value, profile, lang=lang)
        except ValueError:
            # CAN CHANGE TEXT
            await callback.answer(t(lang, 'profile.please_answer_the_current_question_using_its_buttons'), show_alert=True)
            return
        profile = await store_answer(callback.from_user.id, state, profile, editing, field, value)
        lang = profile.get("language") or lang
        if field == "language" and not editing:
            await set_chat_commands(callback.bot, callback.from_user.id, lang)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    if callback.data != "profile:back:reminder_period":
        await show_profile_answer(callback.message, field, value, lang=lang)
    if field == "reminder_hour" and callback.data != "profile:back:reminder_period":
        await show_setup_complete(callback.message, profile, lang=lang)
    else:
        await show_profile_question(callback.message, profile, lang=lang)


@router.message(F.text & ~F.text.startswith("/"))
async def answer_profile_text(message: Message, state: FSMContext):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    language_draft = await state.get_data()
    lang = language_draft.get("profile_answers", {}).get("language") or lang
    if message.from_user is None or message.chat.type != "private":
        return
    if await state.get_state() == ProfileEdit.timezone.state:
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'profile.please_choose_a_time_zone_using_the_buttons_or'))
        return
    profile, editing = await current_answers(message.from_user.id, state, profile=language_profile)
    if profile is None or (not editing and profile["setup_complete"]):
        return
    field = next_profile_field(profile)
    if field == "nickname":
        value = message.text.strip()
        if not 1 <= len(value) <= 64:
            # CAN CHANGE TEXT
            await message.answer(t(lang, 'profile.please_write_a_nickname_between_1_and_64_characters'))
            return
    elif field == "birth_year":
        # Сохранено для возврата отключённого вопроса в PROFILE_QUESTIONS.
        try:
            value = int(message.text.strip())
            if not 1900 <= value <= date.today().year:
                raise ValueError
        except ValueError:
            # CAN CHANGE TEXT
            await message.answer(t(lang, 'profile.please_enter_a_year_from_1900_to_date', date=date.today().year))
            return
    else:
        # CAN CHANGE TEXT
        await message.answer(t(lang, 'profile.please_use_the_buttons_for_the_current_question'))
        return
    profile = await store_answer(message.from_user.id, state, profile, editing, field, value)
    await show_profile_answer(message, field, value, lang=lang)
    await show_profile_question(message, profile, lang=lang)


@router.message(Command("language"))
async def choose_language(message: Message):
    if message.from_user is None or message.chat.type != "private":
        return
    profile = await get_user_profile(message.from_user.id)
    lang = language_of(profile)
    # CAN CHANGE TEXT: названия языков всегда на их собственном языке.
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Русский", callback_data="language:ru"),
        InlineKeyboardButton(text="English", callback_data="language:en"),
    ]])
    await message.answer(t(lang, "language.choose"), reply_markup=keyboard)


@router.callback_query(F.data.startswith("language:"))
async def save_language(callback: CallbackQuery):
    if not isinstance(callback.message, Message) or callback.message.chat.type != "private" or callback.message.chat.id != callback.from_user.id:
        await callback.answer()
        return
    lang = callback.data.removeprefix("language:")
    profile = await get_user_profile(callback.from_user.id)
    if lang not in ("ru", "en"):
        await callback.answer(t(language_of(profile), "language.invalid"), show_alert=True)
        return
    if profile is None:
        await ensure_user_profile(callback.from_user.id, callback.message.chat.id)
    # Меняем только существующее поле: состояние опроса и напоминания остаются.
    await save_profile_answer(callback.from_user.id, "language", lang)
    await set_chat_commands(callback.bot, callback.from_user.id, lang)
    await callback.answer()
    await callback.message.edit_text(t(lang, "language.saved", language={"ru":"Русский", "en":"English"}[lang]), reply_markup=None)
