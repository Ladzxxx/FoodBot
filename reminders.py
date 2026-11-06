from localization import t, language_of
import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError

from database import disable_reminders, get_reminder_profiles, reserve_reminder, get_user_profile
from privacy_access import user_lock
from privacy_storage import has_consent
from Keyboards.morning import morning_open_keyboard
from Keyboards.day import reminder_keyboard
from morning_storage import morning_entry_needed

logger = logging.getLogger(__name__)


def reminder_note_date(profile: dict, now: datetime) -> date:
    local_date = now.astimezone(timezone(timedelta(hours=profile["utc_offset"]))).date()
    if profile["reminder_period"] == "morning":
        return local_date - timedelta(days=1)
    return local_date


async def send_reminder(bot: Bot, chat_id: int, selected_date: date, lang="en", *, morning_date=None, nickname=""):
    # CAN CHANGE TEXT: текст штатного напоминания.
    name = nickname or t(lang, "reminders.friend")
    text = t(lang, "reminders.morning_greeting" if morning_date else "reminders.evening_greeting", nickname=name)
    await bot.send_message(chat_id=chat_id, text=text, parse_mode=None, reply_markup=morning_open_keyboard(morning_date, lang) if morning_date else reminder_keyboard(selected_date, lang=lang))


def reminder_day(profile: dict, now: datetime, lang="en") -> date | None:
    user_timezone = timezone(timedelta(hours=profile["utc_offset"]))
    local_now = now.astimezone(user_timezone)
    last_entry = profile["last_entry_at"]
    if last_entry is None:
        last_entry = profile["reminder_started_at"]
    if profile["reminder_period"] != "morning" and (last_entry is None or now.timestamp() - last_entry < 24 * 60 * 60):
        return None
    if local_now.hour < profile["reminder_hour"]:
        return None
    if profile["last_reminder_date"] == local_now.date().isoformat():
        return None
    return reminder_note_date(profile, now)


async def send_due_reminders(bot: Bot, now: datetime | None = None, lang="en"):
    if now is None:
        now = datetime.now(timezone.utc)
    profiles = await get_reminder_profiles()
    for snapshot in profiles:
        async with user_lock(snapshot["user_id"]):
            # Отказ/удаление и фактическая отправка не выполняются одновременно.
            profile = await get_user_profile(snapshot["user_id"])
            if not profile or not profile["setup_complete"] or not profile["reminders_enabled"]:
                continue
            if not await has_consent(profile["user_id"]):
                continue
            lang = language_of(profile)
            selected_date = reminder_day(profile, now, lang=lang)
            if selected_date is None:
                continue
            local_now = now.astimezone(timezone(timedelta(hours=profile["utc_offset"])))
            local_date = local_now.date().isoformat()
            if profile["reminder_period"] == "morning" and not await morning_entry_needed(profile["user_id"], local_now.date()):
                continue
            reserved = await reserve_reminder(
                profile["user_id"], local_date, int(now.timestamp()) - 86400, expected_profile=profile,
                check_inactivity=profile["reminder_period"] != "morning"
            )
            if not reserved:
                continue
            try:
                morning_date = local_now.date() if profile["reminder_period"] == "morning" else None
                await send_reminder(bot, profile["chat_id"], selected_date, lang=lang, morning_date=morning_date, nickname=profile.get("nickname") or "")
            except TelegramForbiddenError:
                await disable_reminders(profile["user_id"])
            except TelegramAPIError as error:
                # Не повторяем сомнительную отправку в тот же день: сообщение могло дойти.
                logger.warning(t(lang, 'reminders.reminder_failed_for_user_s_s'),
                    profile["user_id"], type(error).__name__)



async def reminder_loop(bot: Bot, lang="en"):
    while True:
        try:
            await send_due_reminders(bot, lang=lang)
        except Exception:
            # CAN CHANGE TEXT
            logger.exception(t(lang, 'reminders.could_not_check_reminders'))
        await asyncio.sleep(60)
