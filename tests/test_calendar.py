import asyncio
import sqlite3
import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch

import aiosqlite
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import DeleteMessage, EditMessageText
from aiogram.types import ReplyKeyboardMarkup

import database
from day_storage import add_meal, get_month_entries, save_day_answer
from helpers import BotTests, day_buttons


class CalendarTests(BotTests):
    async def test_all_calendar_commands_are_neutral(self):
        for command in ("/start", "/callendar"):
            await self.command(command)
            self.assertIn("Select a day", self.screen_text())
            self.assertNotIn("Selected day:", self.screen_text())
            self.assertNotIn("Sleep time:", self.screen_text())
            self.assertNotIn("Edit the day", [b.text for row in self.keyboard().inline_keyboard for b in row])
            self.assertIsNotNone(self.button_data("Statistics"))
            menu = self.screens[self.message_events[-2][1]]["keyboard"]
            self.assertIsInstance(menu, ReplyKeyboardMarkup)
            self.assertEqual([[button.text for button in row] for row in menu.keyboard], [
                ["/meal", "/callendar", "/settings"],
            ])
            self.assertTrue(menu.is_persistent)
            self.assertTrue(menu.resize_keyboard)
            self.assertFalse(menu.one_time_keyboard)

    async def test_current_month_has_only_today_and_past_buttons(self):
        with patch("Handlers.routes.today_for_user", return_value=date(2026, 11, 1)):
            await self.command("/callendar")
            self.assertEqual(list(day_buttons(self.keyboard())), ["2026-11-01"])
            self.assertEqual(self.keyboard().inline_keyboard[0][2].callback_data, "calendar:ignore")
            await self.click("calendar:day:2026-11-01")
            self.assertIn("Selected day: 01.11.2026", self.screen_text())
            self.assertEqual(self.button_data("Edit the day"), "day:edit:2026-11-01")

    async def test_future_date_and_month_callbacks_are_rejected(self):
        with (
            patch("Handlers.routes.today_for_user", return_value=date(2026, 11, 1)),
            patch("Handlers.day.today_for_user", return_value=date(2026, 11, 1)),
            patch("Handlers.statistics.today_for_user", return_value=date(2026, 11, 1)),
        ):
            for data in (
                "calendar:day:2026-11-02", "calendar:month:2026-12-01",
                "day:edit:2026-11-02", "statistics:month:2026-12-01",
            ):
                await self.click(data)
                self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
            self.send.assert_not_called()
            self.assertIsNone(await self.state.get_state())
            self.assertEqual(await get_month_entries(100, 2026, 11), {})

    async def test_user_timezone_controls_which_day_is_today(self):
        fixed = datetime(2026, 11, 1, 0, 30, tzinfo=timezone.utc)
        with patch("Handlers.routes.datetime") as clock:
            clock.now.side_effect = lambda zone: fixed.astimezone(zone)
            async with aiosqlite.connect(database.DB_PATH) as db:
                await db.execute("UPDATE user_profiles SET utc_offset = -11 WHERE user_id = 100")
                await db.commit()
            await self.command("/callendar")
            self.assertIn("2026-10-31", day_buttons(self.keyboard()))
            await self.click("calendar:day:2026-11-01")
            self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
            async with aiosqlite.connect(database.DB_PATH) as db:
                await db.execute("UPDATE user_profiles SET utc_offset = 12 WHERE user_id = 100")
                await db.commit()
            await self.command("/callendar")
            self.assertEqual(list(day_buttons(self.keyboard())), ["2026-11-01"])

    async def test_selected_day_panel_contains_only_requested_properties(self):
        await self.finish_edit(values=(8, 7))
        await save_day_answer(100, date(2024, 2, 12), "day_comment", "Private daily note", "complete")
        await save_day_answer(100, date(2024, 2, 12), "pain_comment", "Private pain note", "complete")
        await self.click("calendar:day:2024-02-12")
        text = self.screen_text()
        for line in (
            "Selected day: 12.02.2024", "Sleep time: 21:00 – 08:00",
            "Sleep satisfaction: 8/10", "Mood stability: 7/10", "Stomach pain: No",
        ):
            self.assertIn(line, text)
        self.assertIn('Private daily note', text)
        for hidden in ("Food:", "Private pain note", "Pain intensity:", "Medication"):
            self.assertNotIn(hidden, text)
        await self.click("calendar:day:2024-02-13")
        self.assertIn("Sleep time: ___ – ___", self.screen_text())
        self.assertIn("Stomach pain: ___", self.screen_text())

    async def test_old_long_day_comment_is_shortened_only_on_screen(self):
        note = 'a' * 250
        await save_day_answer(100, date(2024, 2, 12), 'day_comment', note, 'complete')
        await self.click('calendar:day:2024-02-12')
        self.assertEqual(self.screen_text().split('Day comment:\n')[1], 'a' * 200)
        self.assertEqual((await self.read_entry())['day_comment'], note)

    async def test_viewing_and_statistics_do_not_write(self):
        await self.finish_edit()
        observer = sqlite3.connect(database.DB_PATH)
        try:
            before = observer.execute("PRAGMA data_version").fetchone()[0]
            for data in ("calendar:day:2024-02-12", "calendar:day:2024-02-13", "calendar:month:2024-01-01", "statistics:month:2024-02-12"):
                await self.click(data)
            await self.command("/callendar")
            self.assertEqual(before, observer.execute("PRAGMA data_version").fetchone()[0])
        finally:
            observer.close()

    async def test_calendar_replacement_deletes_first(self):
        await self.command("/callendar")
        old_id = self.current_message_id
        await self.click("calendar:day:2024-02-12")
        self.assertNotIn(old_id, self.screens)
        self.assertEqual(self.message_events[-2:], [("delete", old_id), ("send", self.current_message_id)])

    async def test_undeletable_calendar_is_reused(self):
        await self.command("/callendar")
        old_id = self.current_message_id
        self.delete.side_effect = TelegramBadRequest(
            method=DeleteMessage(chat_id=100, message_id=old_id), message="Bad Request: message can't be deleted"
        )
        self.send.reset_mock()
        await self.click("calendar:day:2024-02-12")
        self.assertEqual(self.current_message_id, old_id)
        self.send.assert_not_called()
        self.assertIn("Selected day: 12.02.2024", self.screen_text())

    async def test_month_navigation_is_neutral_and_crosses_years(self):
        await self.click("calendar:day:2024-12-12")
        await self.click(self.keyboard().inline_keyboard[0][2].callback_data)
        self.assertIn("January 2025", self.screen_text())
        self.assertNotIn("Selected day:", self.screen_text())
        await self.click(self.keyboard().inline_keyboard[0][0].callback_data)
        self.assertIn("December 2024", self.screen_text())
        await self.click("calendar:month:0001-01-01")
        self.assertEqual(self.keyboard().inline_keyboard[0][0].callback_data, "calendar:ignore")

    async def test_leap_year_grids_and_callback_sizes(self):
        for year, count in ((2024, 29), (2025, 28), (1900, 28), (2000, 29)):
            await self.click(f"calendar:month:{year}-02-01")
            self.assertEqual(len(day_buttons(self.keyboard())), count)
            for week in self.keyboard().inline_keyboard[2:-1]:
                self.assertEqual(len(week), 7)
                for weekday, button in enumerate(week):
                    self.assertLessEqual(len(button.callback_data.encode("utf8")), 64)
                    if button.callback_data.startswith("calendar:day:"):
                        self.assertEqual(date.fromisoformat(button.callback_data.split(":")[2]).weekday(), weekday)

    async def test_markers_do_not_convert_old_ratings_or_partial_entries(self):
        await self.finish_edit(day="2024-02-12")
        await database.save_ratings(100, date(2024, 2, 13), 5, 6, 4)
        await self.click("day:edit:2024-02-14")
        await self.click(self.button_data("22:00"))
        await self.click("calendar:month:2024-02-01")
        days = day_buttons(self.keyboard())
        self.assertEqual(days["2024-02-12"], "12 🟨")
        self.assertEqual(days["2024-02-13"], "13")
        self.assertEqual(days["2024-02-14"], "14 📝")
        self.assertEqual(await database.get_legacy_answer(100, date(2024, 2, 10)), 1)
        self.assertEqual((await database.get_month_ratings(100, 2024, 2))["2024-02-13"]["food"], 6)

    async def test_month_statistics_use_new_saved_values(self):
        await self.finish_edit(values=(8, 6))
        await save_day_answer(100, date(2024, 2, 13), "sleep_satisfaction", 10, "mood_control")
        await save_day_answer(100, date(2024, 2, 13), "ache", 1, "pain_intensity")
        await database.save_ratings(100, date(2024, 2, 14), 1, 1, 1)
        await self.finish_edit(day="2024-02-12", values=(1, 1), user_id=200)
        await self.click("statistics:month:2024-02-01")
        for text in ("Days with notes: 5", "Average sleep satisfaction: 9.00/10 (0 below 7)", "Average mood stability: 6.00/10 (1 below 7)", "Days with stomach pain: 1"):
            self.assertIn(text, self.screen_text())
        self.assertNotIn("food", self.screen_text().lower())
        await self.click(self.button_data("Calendar"))
        self.assertNotIn("Selected day:", self.screen_text())

    async def test_all_new_markers_and_no_calendar_legend(self):
        rows = [
            (100, "2024-02-12", "22:00", "05:00", 7, 7, 1),
            (100, "2024-02-13", "22:00", "06:00", 7, 7, 1),
            (100, "2024-02-14", "22:00", "06:00", 6, 7, 1),
            (100, "2024-02-15", "23:00", "08:00", 6, 6, 1),
            (100, "2024-02-16", "23:00", "05:00", 6, 6, 1),
            (100, "2024-02-17", "22:00", "06:00", 8, 8, 0),
        ]
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.executemany("""
                INSERT INTO diary_entries
                    (user_id, entry_date, bedtime, wake_time, sleep_satisfaction, mood_control, completed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, rows)
            await db.commit()
        for day, count in ((12, 2), (13, 1), (14, 1), (15, 1), (16, 1)):
            for index in range(count):
                await add_meal(100, date(2024, 2, day), "12:00", index, 0)
        await self.click("calendar:month:2024-02-01")
        days = day_buttons(self.keyboard())
        for day, marker in ((12, "✅"), (13, "🟨"), (14, "🟧"), (15, "🟥"), (16, "🟥"), (17, "📝")):
            self.assertEqual(days[f"2024-02-{day}"], f"{day} {marker}")
        self.assertEqual(days["2024-02-18"], "18")
        for data in ("calendar:month:2024-02-01", "calendar:day:2024-02-13"):
            await self.click(data)
            self.assertNotIn("requirements", self.screen_text())
            self.assertNotIn("unmet", self.screen_text())
            self.assertNotIn("unfinished draft", self.screen_text())

    async def test_empty_month_statistics_and_invalid_dates(self):
        await self.click("statistics:month:2024-02-01")
        self.assertEqual(self.screen_text().count("No data yet"), 3)
        for data in ("calendar:month:2024-13-01", "calendar:day:2025-02-29", "day:edit:bad-date", "statistics:month:bad"):
            await self.click(data)
            self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])

    async def test_repeated_statistics_acknowledges_unchanged_message(self):
        self.edit.side_effect = TelegramBadRequest(
            method=EditMessageText(chat_id=100, message_id=1, text="Statistics"), message="Bad Request: message is not modified"
        )
        await self.click("statistics:month:2024-02-01")
        self.acknowledge.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
