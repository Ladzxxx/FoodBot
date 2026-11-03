import asyncio
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import aiosqlite
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError
from aiogram.methods import SendMessage

import database
import main
from reminders import send_due_reminders
from helpers import BotTests


class ReminderTests(BotTests):
    async def test_removed_notif_command_does_not_send_a_reminder(self):
        from Handlers.commands import BOT_COMMANDS
        self.assertNotIn('notif', {item.command for item in BOT_COMMANDS})
        await self.add_profile()
        profile = await database.get_user_profile(100)
        await self.command('/notif')
        self.deliver.assert_not_awaited()
        self.assertEqual(await database.get_user_profile(100), profile)

    async def asyncSetUp(self):
        await super().asyncSetUp()
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("DELETE FROM user_profiles")
            await db.commit()
        self.now = datetime(2026, 11, 1, 6, tzinfo=timezone.utc)
        self.deliver = AsyncMock()
        send_patch = patch.object(self.bot, "send_message", self.deliver)
        send_patch.start()
        self.addCleanup(send_patch.stop)

    async def add_profile(self, user_id=100, period="morning", hour=9, offset=3, last_entry=None):
        started = int((self.now - timedelta(days=2)).timestamp())
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("""
                INSERT INTO user_profiles (user_id, chat_id, language, nickname, gender,
                    birth_year, utc_offset, reminder_period, reminder_hour, setup_complete,
                    reminder_started_at, last_entry_at)
                VALUES (?, ?, 'en', 'Tester', 'secret', 2000, ?, ?, ?, 1, ?, ?)
            """, (user_id, user_id, offset, period, hour, started, last_entry))
            await db.commit()

    def reminder_button(self):
        return self.deliver.call_args.kwargs["reply_markup"].inline_keyboard[0][0]

    async def test_morning_reminder_opens_yesterday_and_starts_questions(self):
        await self.add_profile()
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_awaited_once()
        self.assertEqual(self.deliver.call_args.kwargs["text"], "— Hi, it's Me!")
        button = self.reminder_button()
        self.assertEqual(button.text, "Make a note about 31.10.2026")
        self.assertEqual(button.callback_data, "day:edit:2026-10-31")
        await self.click(button.callback_data)
        self.assertIn("Editing day: 31.10.2026", self.screen_text())
        self.assertIn("When did you go to bed?", self.screen_text())

    async def test_evening_reminder_uses_today(self):
        await self.add_profile(period="evening", hour=18)
        now = self.now.replace(hour=15)
        await send_due_reminders(self.bot, now)
        self.assertEqual(self.reminder_button().callback_data, "day:edit:2026-11-01")
        self.assertEqual(self.reminder_button().text, "Make a note about 01.11.2026")

    async def test_no_reminder_before_the_selected_local_hour(self):
        await self.add_profile(hour=10)
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_not_awaited()
        await send_due_reminders(self.bot, self.now + timedelta(hours=1))
        self.deliver.assert_awaited_once()

    async def test_24_hour_inactivity_boundary(self):
        await self.add_profile(last_entry=int((self.now - timedelta(hours=24) + timedelta(seconds=1)).timestamp()))
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_not_awaited()
        await send_due_reminders(self.bot, self.now + timedelta(seconds=1))
        self.deliver.assert_awaited_once()

    async def test_new_profile_waits_24_hours_after_setup(self):
        await self.add_profile()
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("UPDATE user_profiles SET reminder_started_at = ?", (int(self.now.timestamp()),))
            await db.commit()
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_not_awaited()
        await send_due_reminders(self.bot, self.now + timedelta(days=1))
        self.deliver.assert_awaited_once()

    async def test_once_per_local_day_including_restart(self):
        await self.add_profile()
        await send_due_reminders(self.bot, self.now)
        await database.init_db()
        await send_due_reminders(self.bot, self.now + timedelta(minutes=1))
        self.deliver.assert_awaited_once()
        await send_due_reminders(self.bot, self.now + timedelta(days=1))
        self.assertEqual(self.deliver.await_count, 2)

    async def test_saving_any_day_resets_inactivity(self):
        await self.add_profile()
        with patch("day_storage.time", return_value=self.now.timestamp()):
            await self.finish_edit(day="2024-02-12", values=(8, 7))
        await send_due_reminders(self.bot, self.now + timedelta(hours=1))
        self.deliver.assert_not_awaited()
        self.assertEqual((await database.get_user_profile(100))["last_entry_at"], int(self.now.timestamp()))

    async def test_viewing_calendar_does_not_reset_inactivity(self):
        await self.add_profile()
        await self.click("calendar:day:2024-02-12")
        await self.click("statistics:month:2024-02-12")
        self.assertIsNone((await database.get_user_profile(100))["last_entry_at"])
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_awaited_once()

    async def test_timezone_change_rebases_the_reminder_day_without_duplicates(self):
        await self.add_profile()
        await send_due_reminders(self.bot, self.now)
        before = await database.get_user_profile(100)
        with patch.object(database, "time", return_value=self.now.timestamp()):
            await self.command("/timezone")
            await self.click("profile:utc_offset:-11")
        after = await database.get_user_profile(100)
        self.assertEqual(after["last_reminder_date"], "2026-10-31")
        self.assertEqual(after["last_reminder_at"], int(self.now.timestamp()))
        self.assertEqual(after["reminders_enabled"], 1)
        self.assertEqual(after["last_entry_at"], before["last_entry_at"])
        await database.init_db()
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_awaited_once()
        await send_due_reminders(self.bot, self.now + timedelta(hours=14))
        self.assertEqual(self.deliver.await_count, 2)

    async def test_reminders_keep_running_while_settings_are_being_edited(self):
        await self.add_profile()
        await self.command("/settings")
        await self.click("profile:language:ru")
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_awaited_once()
        profile = await database.get_user_profile(100)
        self.assertEqual(profile["language"], "en")
        self.assertEqual(profile["utc_offset"], 3)
        self.assertEqual(profile["reminder_hour"], 9)

    async def test_stale_schedule_cannot_reserve_after_timezone_change(self):
        await self.add_profile()
        old = await database.get_user_profile(100)
        await database.update_user_timezone(100, 12)
        reserved = await database.reserve_reminder(100, "2026-11-01", int(self.now.timestamp()) - 86400, expected_profile=old)
        self.assertFalse(reserved)

    async def test_meals_do_not_reset_the_diary_reminder_timer(self):
        await self.add_profile()
        await self.command("/meal Lunch")
        self.assertIsNone((await database.get_user_profile(100))["last_entry_at"])
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_awaited_once()

    async def test_timezone_change_protects_legacy_date_only_notification(self):
        await self.add_profile()
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("UPDATE user_profiles SET last_reminder_date = '2026-11-01', last_reminder_at = NULL")
            await db.commit()
        with patch.object(database, "time", return_value=self.now.timestamp()):
            await self.command("/timezone")
            await self.click("profile:utc_offset:-11")
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_not_awaited()

    async def test_negative_utc_offset_uses_local_calendar_date(self):
        await self.add_profile(offset=-11, hour=9)
        now = datetime(2026, 11, 1, 0, tzinfo=timezone.utc)
        await send_due_reminders(self.bot, now)
        self.assertEqual(self.reminder_button().callback_data, "day:edit:2026-10-30")

    async def test_incomplete_or_blocked_profiles_receive_no_reminders(self):
        await self.add_profile(user_id=100)
        await self.add_profile(user_id=200)
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("UPDATE user_profiles SET setup_complete = 0 WHERE user_id = 100")
            await db.execute("UPDATE user_profiles SET reminders_enabled = 0 WHERE user_id = 200")
            await db.commit()
        await send_due_reminders(self.bot, self.now)
        self.deliver.assert_not_awaited()

    async def test_blocked_bot_disables_reminders(self):
        await self.add_profile()
        self.deliver.side_effect = TelegramForbiddenError(
            method=SendMessage(chat_id=100, text="test"), message="Forbidden: bot was blocked by the user"
        )
        await send_due_reminders(self.bot, self.now)
        self.assertEqual((await database.get_user_profile(100))["reminders_enabled"], 0)
        await send_due_reminders(self.bot, self.now + timedelta(days=1))
        self.deliver.assert_awaited_once()

    async def test_uncertain_delivery_is_not_repeated_the_same_day(self):
        await self.add_profile()
        self.deliver.side_effect = TelegramNetworkError(
            method=SendMessage(chat_id=100, text="test"), message="Test network failure"
        )
        await send_due_reminders(self.bot, self.now)
        await send_due_reminders(self.bot, self.now + timedelta(minutes=1))
        self.deliver.assert_awaited_once()

    async def test_fresh_entry_prevents_reserving_a_stale_reminder(self):
        await self.add_profile()
        with patch("day_storage.time", return_value=self.now.timestamp()):
            await self.finish_edit(day="2026-11-01", values=(8, 7))
        reserved = await database.reserve_reminder(100, "2026-11-01", int(self.now.timestamp()) - 86400)
        self.assertFalse(reserved)

    async def test_startup_cancels_worker_before_closing_bot_session(self):
        events = []

        async def worker(bot):
            events.append("worker started")
            try:
                await asyncio.Event().wait()
            finally:
                events.append("worker stopped")

        async def polling(bot, **kwargs):
            self.assertFalse(kwargs["close_bot_session"])
            await asyncio.sleep(0)

        async def close_session():
            events.append("session closed")

        with (
            patch.object(main, "load_dotenv"),
            patch.object(main, "getenv", return_value="123456:TEST_TOKEN"),
            patch.object(main, "init_db", new_callable=AsyncMock),
            patch.object(main, "Bot", return_value=self.bot),
            patch.object(main, "reminder_loop", worker),
            patch.object(main.dispatcher, "start_polling", side_effect=polling),
            patch.object(self.bot.session, "close", side_effect=close_session),
        ):
            await main.main()
        self.assertEqual(events, ["worker started", "worker stopped", "session closed"])


if __name__ == "__main__":
    unittest.main()
