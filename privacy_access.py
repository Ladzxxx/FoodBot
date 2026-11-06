from weakref import WeakValueDictionary
import asyncio

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from database import get_user_profile
from Forms.privacy import PrivacySetup
from localization import language_of, t
from privacy_storage import has_consent, pending_deletions

# Один процесс polling на токен. Та же блокировка используется отправкой напоминаний.
# Слабые ссылки не сохраняют список отказавшихся пользователей.
_user_locks = WeakValueDictionary()


def user_lock(user_id):
    lock = _user_locks.get(user_id)
    if lock is None:
        lock = asyncio.Lock()
        _user_locks[user_id] = lock
    return lock


class PrivacyAccess(BaseMiddleware):
    # Единственная общая проверка: иначе старый callback мог бы обойти согласие.
    async def __call__(self, handler, event, data):
        user = event.from_user
        message = event.message if isinstance(event, CallbackQuery) else event
        if user is None or not isinstance(message, Message):
            if isinstance(event, CallbackQuery):
                await event.answer()
            return
        if message.chat.type != "private" or message.chat.id != user.id:
            if isinstance(event, CallbackQuery):
                await event.answer()
            return
        async with user_lock(user.id):
            state = data["state"]
            current = await state.get_state()
            if isinstance(event, Message):
                command = (event.text or "").split(maxsplit=1)[0].split("@")[0].lower() if event.text else ""
                if command in ("/start", "/privacy", "/delete_me"):
                    return await handler(event, data)
            elif (event.data or "").startswith("privacy:"):
                return await handler(event, data)
            if await has_consent(user.id):
                return await handler(event, data)
            profile = await get_user_profile(user.id)
            if user.id in pending_deletions:
                text = t(language_of(profile), "privacy.delete_failed")
                if isinstance(event, CallbackQuery):
                    await event.answer(text, show_alert=True)
                else:
                    await event.answer(text)
                return
            lang = language_of(profile)
            draft = await state.get_data()
            lang = draft.get("privacy_lang") or lang
            if isinstance(event, CallbackQuery):
                await event.answer(t(lang, "privacy.start_required"), show_alert=True)
            # Только существующему пользователю предлагаем политику при первом действии.
            # После отказа профиля нет: произвольный текст не создаёт его заново.
            if profile and current not in (PrivacySetup.language.state, PrivacySetup.consent.state):
                from Handlers.privacy import show_consent
                await show_consent(message, state, lang)
            elif isinstance(event, Message):
                await event.answer(t(lang, "privacy.start_required"))
