import logging
from secrets import token_hex

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database import ensure_user_profile, get_user_profile, save_profile_answer
from Forms.privacy import PrivacySetup
from Keyboards.privacy import consent_keyboard, delete_keyboard, privacy_language_keyboard
from localization import first_language, language_of, t
from privacy_storage import (
    CONSENT_VERSION, POLICY_VERSION, accept_consent, delete_user_data, has_consent, pending_deletions,
)

router = Router()
logger = logging.getLogger(__name__)


async def remove_buttons(message):
    try:
        await message.edit_reply_markup(reply_markup=None)
    except TelegramAPIError:
        # Старое сообщение Telegram может быть недоступно; nonce всё равно истёк.
        pass


async def show_policy(message, lang):
    await message.answer(t(lang, "privacy.policy", version=POLICY_VERSION))


async def show_consent(message, state, lang):
    await state.clear()
    await show_policy(message, lang)
    token = token_hex(6)
    question = await message.answer(
        t(lang, "privacy.consent"), reply_markup=consent_keyboard(token, lang))
    await state.set_state(PrivacySetup.consent)
    await state.set_data({
        "privacy_lang": lang, "privacy_token": token,
        "privacy_message_id": question.message_id,
        "policy_version": POLICY_VERSION, "consent_version": CONSENT_VERSION,
    })


@router.message(Command("start"))
async def start(message: Message, state):
    if message.from_user.id in pending_deletions:
        profile = await get_user_profile(message.from_user.id)
        await message.answer(t(language_of(profile), "privacy.delete_failed"))
        return
    if await has_consent(message.from_user.id):
        from Handlers.profile import start as profile_start
        await profile_start(message, state)
        return
    profile = await get_user_profile(message.from_user.id)
    lang = language_of(profile) if profile else first_language(message.from_user)
    await state.clear()
    token = token_hex(6)
    await message.answer(t(lang, "privacy.welcome"), reply_markup=ReplyKeyboardRemove())
    question = await message.answer(t(lang, "privacy.choose_language"),
        reply_markup=privacy_language_keyboard(token))
    await state.set_state(PrivacySetup.language)
    await state.set_data({"privacy_token": token, "privacy_message_id": question.message_id})


@router.message(Command("privacy"))
async def privacy(message: Message, state):
    profile = await get_user_profile(message.from_user.id)
    draft = await state.get_data()
    await show_policy(message, draft.get("privacy_lang") or language_of(profile))


@router.message(Command("delete_me"))
async def ask_delete(message: Message, state):
    profile = await get_user_profile(message.from_user.id)
    draft = await state.get_data()
    lang = draft.get("privacy_lang") or language_of(profile)
    token = token_hex(6)
    # Не меняем черновик до подтверждения удаления.
    question = await message.answer(t(lang, "privacy.delete_question"),
        reply_markup=delete_keyboard(token, lang))
    await state.update_data(delete_token=token, delete_message_id=question.message_id, delete_lang=lang)


async def finish_deletion(message, user_id, state, lang, declined=False):
    await state.clear()
    pending_deletions.add(user_id)
    try:
        await delete_user_data(user_id)
    except Exception as error:
        # Не выводим содержимое сообщений/SQLite, только тип ошибки.
        logger.error("User data deletion failed: %s", type(error).__name__)
        await message.answer(t(lang, "privacy.delete_failed"), reply_markup=ReplyKeyboardRemove())
        return
    await remove_buttons(message)
    await message.answer(t(lang, "privacy.declined" if declined else "privacy.deleted"),
        reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data.startswith("privacy:"))
async def privacy_button(callback: CallbackQuery, state):
    draft = await state.get_data()
    profile = await get_user_profile(callback.from_user.id)
    lang = draft.get("privacy_lang") or language_of(profile)
    parts = callback.data.split(":")
    action = parts[1] if len(parts) > 1 else ""
    token = parts[2] if len(parts) > 2 else ""
    current = await state.get_state()
    if action in ("delete", "cancel"):
        valid = (len(parts) == 3 and token == draft.get("delete_token")
            and callback.message.message_id == draft.get("delete_message_id"))
        lang = draft.get("delete_lang") or lang
    else:
        valid = (token == draft.get("privacy_token")
            and callback.message.message_id == draft.get("privacy_message_id"))
        if action == "lang":
            valid = valid and len(parts) == 4 and current == PrivacySetup.language.state and parts[3] in ("ru", "en")
        else:
            valid = (valid and len(parts) == 3 and action in ("agree", "decline")
                and current == PrivacySetup.consent.state
                and draft.get("policy_version") == POLICY_VERSION
                and draft.get("consent_version") == CONSENT_VERSION)
    if action == "agree" and callback.from_user.id in pending_deletions:
        await callback.answer(t(lang, "privacy.delete_failed"), show_alert=True)
        return
    if not valid:
        await callback.answer(t(lang, "privacy.expired"), show_alert=True)
        return
    await callback.answer()
    await remove_buttons(callback.message)
    if action == "lang":
        await show_consent(callback.message, state, parts[3])
    elif action == "agree":
        await accept_consent(callback.from_user.id, lang)
        await ensure_user_profile(callback.from_user.id, callback.message.chat.id)
        await save_profile_answer(callback.from_user.id, "language", lang)
        await state.clear()
        await callback.message.answer(t(lang, "privacy.accepted"))
        from Handlers.profile import start as profile_start
        # Message в callback отправлено ботом; для /start нужен реальный пользователь.
        user_message = callback.message.model_copy(update={"from_user": callback.from_user})
        await profile_start(user_message, state)
    elif action in ("decline", "delete"):
        await finish_deletion(callback.message, callback.from_user.id, state, lang, action == "decline")
    elif action == "cancel":
        await state.update_data(delete_token=None, delete_message_id=None, delete_lang=None)
        await callback.message.answer(t(lang, "privacy.delete_cancelled"))
