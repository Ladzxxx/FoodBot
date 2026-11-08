import unittest
import sqlite3
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import aiosqlite

import database
from day_storage import add_medication, get_day_entry, get_meals, reset_day_draft, save_day_answer, save_medication_relief
from Forms.day import DayEdit, has_green_marker, sleep_minutes
from Forms.profile import ProfileEdit
from Handlers.commands import BOT_COMMANDS, set_bot_commands
from Handlers.day import entry_day_label
from helpers import BotTests


class CommandTests(BotTests):
    async def test_native_command_menu_contains_every_requested_command(self):
        await set_bot_commands(self.bot)
        self.assertEqual(self.bot.set_my_commands.await_count, 3)
        self.bot.set_chat_menu_button.assert_awaited_once()
        self.assertEqual({item.command for item in BOT_COMMANDS}, {
            "settings", "callendar", "start", "statistics", "help", "timezone", "meal", "makenote",
            "language", "privacy", "delete_me",
        })

    async def test_start_and_callendar_leave_any_dialogue_without_erasing_notes(self):
        for command in ("/start", "/callendar"):
            await self.open_day_edit()
            if (await self.state.get_data())["step"] == "bedtime":
                await self.click(self.button_data("21:00"))
            before = await self.read_entry()
            await self.command(command)
            self.assertIsNone(await self.state.get_state())
            self.assertIn("Select a day", self.screen_text())
            self.assertEqual(await self.read_entry(), before)

    async def test_help_is_available_during_a_question_and_keeps_progress(self):
        await self.open_day_edit()
        question_id = self.current_message_id
        button = self.button_data("21:00")
        await self.command("/help")
        self.assertIn("/meal", self.screen_text())
        self.assertIn("/settings", self.screen_text())
        self.assertEqual(await self.state.get_state(), DayEdit.answer.state)
        await self.click(button, message_id=question_id)
        self.assertEqual((await self.read_entry())["bedtime"], "21:00")

    async def test_settings_keep_saved_profile_until_last_answer(self):
        original = await database.get_user_profile(100)
        await self.command("/settings")
        self.assertEqual(await self.state.get_state(), ProfileEdit.settings.state)
        await self.click("profile:language:ru")
        await self.command("New nickname")
        await self.click("profile:utc_offset:5")
        await self.click("profile:reminder_period:evening")
        self.assertEqual(await database.get_user_profile(100), original)
        await self.click(self.button_data("Назад"))
        self.assertEqual(await database.get_user_profile(100), original)
        await self.click("profile:reminder_period:morning")
        await self.click("profile:reminder_hour:10")
        profile = await database.get_user_profile(100)
        for field, expected in {"language": "ru", "nickname": "New nickname", "gender": original['gender'], "birth_year": original['birth_year'], "utc_offset": 5, "reminder_period": "morning", "reminder_hour": 10}.items():
            self.assertEqual(profile[field], expected)
        for field in ("last_entry_at", "reminder_started_at", "reminders_enabled", "setup_complete"):
            self.assertEqual(profile[field], original[field])

    async def test_leaving_settings_or_timezone_keeps_original_preferences(self):
        original = await database.get_user_profile(100)
        await self.command("/settings")
        await self.click("profile:language:ru")
        await self.command("/start")
        self.assertEqual(await database.get_user_profile(100), original)
        await self.command("/timezone")
        await self.command("/callendar")
        self.assertEqual(await database.get_user_profile(100), original)

    async def test_timezone_command_only_changes_the_offset(self):
        original = await database.get_user_profile(100)
        await self.command("/timezone")
        await self.click("profile:utc_offset:-11")
        profile = await database.get_user_profile(100)
        self.assertEqual(profile["utc_offset"], -11)
        for field in ("nickname", "gender", "birth_year", "reminder_period", "reminder_hour", "last_entry_at", "reminder_started_at", "reminders_enabled"):
            self.assertEqual(profile[field], original[field])
        self.assertIsNone(await self.state.get_state())
        self.assertIn("Time zone: -11:00 UTC", self.screen_text())

    async def test_continue_or_clean_draft_is_an_explicit_choice(self):
        await self.open_day_edit()
        await self.click(self.button_data("22:00"))
        await self.command("/callendar")
        await self.click("day:edit:2024-02-12")
        self.assertEqual(await self.state.get_state(), DayEdit.choose.state)
        self.assertIsNotNone(self.button_data("Continue draft"))
        clean = self.button_data("Start clean")
        await self.click(self.button_data("Continue draft"))
        self.assertIn("What time did you wake up today?", self.screen_text())
        await self.click(clean)
        self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
        self.assertEqual((await self.read_entry())["bedtime"], "22:00")

    async def test_start_clean_removes_only_that_draft_and_its_medications(self):
        await self.open_day_edit()
        await self.click(self.button_data("22:00"))
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("INSERT INTO day_medications (user_id, entry_date, description) VALUES (100, '2024-02-12', 'Old medicine')")
            await db.execute("INSERT INTO meals (user_id, entry_date, meal_time, created_at, utc_offset, comment) VALUES (100, '2024-02-12', '12:00', 1, 0, 'Lunch')")
            await db.commit()
        await save_day_answer(200, date(2024, 2, 12), "bedtime", "21:00", "wake_time")
        await self.command("/callendar")
        await self.click("day:edit:2024-02-12")
        await self.click(self.button_data("Start clean"))
        self.assertIsNone(await self.read_entry())
        self.assertIsNotNone(await get_day_entry(200, date(2024, 2, 12)))
        self.assertEqual(len(await get_meals(100, date(2024, 2, 12))), 1)
        self.assertIn("When did you go to bed?", self.screen_text())
        async with aiosqlite.connect(database.DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM day_medications WHERE user_id = 100") as cursor:
                self.assertEqual((await cursor.fetchone())[0], 0)

    async def test_clean_draft_cannot_delete_a_completed_entry(self):
        await self.finish_edit()
        self.assertFalse(await reset_day_draft(100, date(2024, 2, 12)))
        self.assertEqual((await self.read_entry())["completed"], 1)

    async def test_all_statistics_include_previous_month_and_other_months(self):
        await self.finish_edit(day="2026-10-15", values=(8, 7))
        await self.finish_edit(day="2024-02-12", values=(6, 6))
        await self.finish_edit(day="2024-02-12", values=(1, 1), user_id=200)
        with patch("Handlers.statistics.today_for_user", return_value=date(2026, 11, 1)):
            await self.command("/statistics")
            text = self.screen_text()
            self.assertIn("All-time statistics", text)
            self.assertIn("Previous month: October 2026", text)
            self.assertIn("Days with notes: 4", text)
            self.assertIn("Average sleep satisfaction: 7.00/10", text)
            self.assertIn("Average sleep satisfaction: 7.00/10 (1 below 7)", text)
            self.assertIsNotNone(self.button_data("📊 October 2026"))
            await self.click(self.button_data("Calendar"))
            self.assertNotIn("Selected day:", self.screen_text())

    async def test_green_marker_uses_inclusive_sevens_and_two_meals(self):
        base = {"completed": 1, "bedtime": "22:00", "wake_time": "05:00", "sleep_satisfaction": 7, "mood_control": 7}
        self.assertTrue(has_green_marker(base, 2))
        self.assertEqual(sleep_minutes(base), 420)
        for changes in ({"completed": 0}, {"mood_control": 6}, {"sleep_satisfaction": 6}, {"wake_time": "04:59"}, {"bedtime": None}):
            self.assertFalse(has_green_marker({**base, **changes}, 2), changes)
        self.assertFalse(has_green_marker(base, 0))
        self.assertFalse(has_green_marker(base, 1))
        self.assertTrue(has_green_marker(base, 3))
        self.assertTrue(has_green_marker({**base, "bedtime": "22:59", "wake_time": "05:59"}, 2))
        self.assertFalse(has_green_marker({**base, "bedtime": "23:00", "wake_time": "06:00"}, 2))

    async def test_recorded_month_buttons_are_paged(self):
        for month in range(1, 13):
            await save_day_answer(100, date(2020, month, 12), "bedtime", "21:00", "wake_time")
        await self.command("/statistics")
        self.assertIsNotNone(self.button_data("Months →"))
        await self.click(self.button_data("Months →"))
        self.assertIsNotNone(self.button_data("← Months"))
        await self.click(self.button_data("📊 January 2020"))
        self.assertIn("Statistics: January 2020", self.screen_text())
        self.assertIn("Days with notes: 1", self.screen_text())

    async def test_makenote_is_read_only_and_opens_today_yesterday_and_calendar(self):
        today = date(2026, 11, 2)
        with patch("Handlers.day.today_for_user", return_value=today):
            observer = sqlite3.connect(database.DB_PATH)
            try:
                before = observer.execute("PRAGMA data_version").fetchone()[0]
                await self.command("/makenote")
                self.assertEqual(before, observer.execute("PRAGMA data_version").fetchone()[0])
            finally:
                observer.close()
            self.assertIn("Headache Diary", self.screen_text())
            self.assertIn("No entries yet.", self.screen_text())
            self.assertEqual([len(row) for row in self.keyboard().inline_keyboard], [1, 1, 1])
            for label, day in (("today", today), ("yesterday", today - timedelta(days=1))):
                await self.command("/makenote")
                await self.click(self.button_data(f"Make note for {label} ({day:%d.%m.%Y})"))
                self.assertEqual((await self.state.get_data())["date"], day.isoformat())
                self.assertIn("When did you go to bed", self.screen_text())
            await self.command("/makenote")
            await self.click(self.button_data("View the calendar"))
            self.assertNotIn("Selected day:", self.screen_text())

    async def test_makenote_keeps_drafts_and_uses_existing_draft_choices(self):
        today = date(2026, 11, 2)
        with patch("Handlers.day.today_for_user", return_value=today):
            await self.open_day_edit(today.isoformat())
            await self.click(self.button_data("20:00"))
            before = await self.read_entry(today.isoformat())
            await self.command("/makenote")
            self.assertIsNone(await self.state.get_state())
            self.assertEqual(await self.read_entry(today.isoformat()), before)
            self.assertIn("— 📝", self.screen_text())
            await self.click(self.button_data("Make note for today (02.11.2026)"))
            self.assertIsNotNone(self.button_data("Start clean"))
            await self.click(self.button_data("Continue draft"))
            self.assertEqual((await self.state.get_data())["step"], "wake_time")

    async def test_recent_entries_are_private_sorted_limited_and_use_local_time(self):
        today = date(2026, 11, 2)
        saved = int(datetime(2026, 11, 2, 16, 33, tzinfo=timezone.utc).timestamp())
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("UPDATE user_profiles SET utc_offset = 3 WHERE user_id = 100")
            for index in range(10):
                await db.execute("""
                    INSERT INTO diary_entries
                        (user_id, entry_date, bedtime, wake_time, sleep_satisfaction, mood_control, completed, updated_at)
                    VALUES (100, ?, '22:00', '06:00', 8, 8, 1, ?)
                """, ((today - timedelta(days=index)).isoformat(), saved))
            await db.execute("INSERT INTO diary_entries (user_id, entry_date) VALUES (200, '2026-11-02')")
            await db.execute("INSERT INTO diary_entries (user_id, entry_date) VALUES (100, '2026-11-03')")
            await db.commit()
        with patch("Handlers.day.today_for_user", return_value=today):
            await self.command("/makenote")
        lines = self.screen_text().split("Latest entries:\n")[1].splitlines()
        self.assertEqual(len(lines), 8)
        self.assertEqual(lines[0], "Today, 7:33 PM — 🟨")
        self.assertEqual(lines[1], "Yesterday, 7:33 PM — 🟨")
        self.assertEqual(lines[2], "Saturday, 7:33 PM — 🟨")
        self.assertEqual(lines[-1], "October 26, 7:33 PM — 🟨")
        self.assertEqual(entry_day_label(date(2025, 10, 25), today), "October 25, 2025")

    async def test_old_entries_gain_timestamp_column_without_inventing_times(self):
        day = date(2024, 2, 12)
        await save_day_answer(100, day, "bedtime", "22:00", "wake_time")
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("ALTER TABLE diary_entries DROP COLUMN updated_at")
            await db.execute("ALTER TABLE diary_entries DROP COLUMN bedtime_day")
            await db.commit()
        await database.init_db()
        entry = await self.read_entry()
        self.assertEqual(entry["bedtime"], "22:00")
        self.assertEqual(entry["bedtime_day"], -1)
        self.assertIsNone(entry["updated_at"])
        await self.command("/makenote")
        self.assertIn("February 12, 2024, Time not recorded — 📝", self.screen_text())
        await database.init_db()
        self.assertEqual(await self.read_entry(), entry)

    async def test_all_diary_answer_types_update_timestamp_without_meal_side_effects(self):
        day = date(2024, 2, 12)
        with patch("day_storage.time", return_value=1000):
            await save_day_answer(100, day, "bedtime", "22:00", "wake_time")
        self.assertEqual((await self.read_entry())["updated_at"], 1000)
        with patch("day_storage.time", return_value=2000):
            await add_medication(100, day, "Test medicine, one tablet", replace_existing=False)
        self.assertEqual((await self.read_entry())["updated_at"], 2000)
        with patch("day_storage.time", return_value=3000):
            await save_medication_relief(100, day, "yes")
        self.assertEqual((await self.read_entry())["updated_at"], 3000)
        await self.command("/meal Lunch")
        self.assertEqual((await self.read_entry())["updated_at"], 3000)

    async def test_new_user_makenote_requests_setup_without_writing_a_day(self):
        await self.command("/makenote", user_id=200)
        self.assertIn("/start", self.screen_text())
        self.assertIsNone(await database.get_user_profile(200))


if __name__ == "__main__":
    unittest.main()
