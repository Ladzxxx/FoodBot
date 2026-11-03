from localization import t, language_of
import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError

from database import disable_reminders, get_reminder_profiles, reserve_reminder
from Keyboards.day import reminder_keyboard

logger = logging.getLogger(__name__)


def reminder_note_date(profile: dict, now: datetime) -> date:
    local_date = now.astimezone(timezone(timedelta(hours=profile["utc_offset"]))).date()
    if profile["reminder_period"] == "morning":
        return local_date - timedelta(days=1)
    return local_date


async def send_reminder(bot: Bot, chat_id: int, selected_date: date, lang="en"):
    # CAN CHANGE TEXT: текст штатного напоминания.
    await bot.send_message(chat_id=chat_id, text=t(lang, 'reminders.hi_it_s_me'), reply_markup=reminder_keyboard(selected_date, lang=lang))


def reminder_day(profile: dict, now: datetime, lang="en") -> date | None:
    user_timezone = timezone(timedelta(hours=profile["utc_offset"]))
    local_now = now.astimezone(user_timezone)
    last_entry = profile["last_entry_at"]
    if last_entry is None:
        last_entry = profile["reminder_started_at"]
    if last_entry is None or now.timestamp() - last_entry < 24 * 60 * 60:
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
    for profile in profiles:
        lang = language_of(profile)
        selected_date = reminder_day(profile, now, lang=lang)
        if selected_date is None:
            continue
        local_now = now.astimezone(timezone(timedelta(hours=profile["utc_offset"])))
        local_date = local_now.date().isoformat()
        reserved = await reserve_reminder(
            profile["user_id"], local_date, int(now.timestamp()) - 86400, expected_profile=profile
        )
        if not reserved:
            continue
        try:
            await send_reminder(bot, profile["chat_id"], selected_date, lang=lang)
        except TelegramForbiddenError:
            await disable_reminders(profile["user_id"])
        except TelegramAPIError as error:
            # Не повторяем сомнительную отправку в тот же день: сообщение могло дойти.
            # CAN CHANGE TEXT
            logger.warning(t(lang, 'reminders.reminder_failed_for_user_s_s'), profile["user_id"], type(error).__name__)


async def reminder_loop(bot: Bot, lang="en"):
    while True:
        try:
            await send_due_reminders(bot, lang=lang)
        except Exception:
            # CAN CHANGE TEXT
            logger.exception(t(lang, 'reminders.could_not_check_reminders'))
        await asyncio.sleep(60)
