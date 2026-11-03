import sqlite3
import unittest
from datetime import date
from unittest.mock import patch

import aiosqlite

import database
from day_storage import add_meal, get_meal_counts, save_day_answer
from helpers import BotTests, day_buttons


class StatisticsTests(BotTests):
    async def test_requested_month_summary_and_bold_headings(self):
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.executemany("""
                INSERT INTO diary_entries
                    (user_id, entry_date, bedtime, wake_time, sleep_satisfaction, mood_control, ache, completed)
                VALUES (100, ?, ?, ?, ?, ?, 0, 1)
            """, [
                ("2026-11-01", "22:00", "07:00", 8, 5),
                ("2026-11-02", "23:00", "08:00", 9, 7),
            ])
            await db.commit()
        for index in range(5):
            await add_meal(100, date(2026, 11, 1), "12:00", index, 0)
        with patch("Handlers.statistics.today_for_user", return_value=date(2026, 11, 2)):
            await self.click("statistics:month:2026-11-01")
        self.assertEqual(self.screen_text(), (
            "📊 Statistics: November 2026\n\n"
            "Days with notes: 2\n\n"
            "Average sleep duration: 9 h 00 min\n"
            "Average sleep satisfaction: 8.50/10 (0 below 7)\n"
            "Average mood stability: 6.00/10 (1 below 7)\n"
            "Days with stomach pain: 0\n\n"
            "✅ Excellent days: 0\n"
            "🍽 Meal notes: 5"
        ))
        screen = self.screens[self.current_message_id]
        self.assertEqual(screen["parse_mode"], "HTML")
        self.assertIn("<b>📊 Statistics: November 2026</b>", screen["text"])
        self.assertEqual(self.button_data("October 2026"), "statistics:month:2026-10-01")
        self.assertIsNotNone(self.button_data("Meal statistics"))

    async def test_previous_month_crosses_year_and_calendar_returns_to_that_month(self):
        await self.click("statistics:month:2025-01-01")
        await self.click(self.button_data("December 2024"))
        self.assertIn("Statistics: December 2024", self.screen_text())
        await self.click(self.button_data("Calendar"))
        self.assertIn("December 2024", self.screen_text())
        self.assertNotIn("Selected day:", self.screen_text())
        await self.click("statistics:month:0001-01-01")
        self.assertEqual([button.text for row in self.keyboard().inline_keyboard for button in row], ["Meal statistics", "Pain statistics", "Get Excel file", "Calendar"])

    async def test_meal_statistics_button_is_read_only_and_keeps_active_question(self):
        await self.click("statistics:month:2024-02-01")
        statistics_id = self.current_message_id
        placeholder = self.button_data("Meal statistics")
        await self.command("/callendar")
        await self.open_day_edit()
        await self.click(self.button_data("21:00"))
        active_id = self.current_message_id
        state_before = await self.state.get_state()
        data_before = await self.state.get_data()
        observer = sqlite3.connect(database.DB_PATH)
        try:
            version = observer.execute("PRAGMA data_version").fetchone()[0]
            for _ in range(2):
                await self.click(placeholder, message_id=statistics_id)
            self.assertEqual(observer.execute("PRAGMA data_version").fetchone()[0], version)
        finally:
            observer.close()
        self.assertEqual(self.current_message_id, active_id)
        self.assertEqual(await self.state.get_state(), state_before)
        self.assertEqual(await self.state.get_data(), data_before)
        self.assertTrue(self.acknowledge.called)

    async def test_second_meal_updates_calendar_diary_and_statistics_without_editing_answers(self):
        day = date(2024, 2, 12)
        await self.finish_edit(values=(7, 7))
        saved_entry = await self.read_entry()
        await add_meal(200, day, "12:00", 1, 0)
        await add_meal(200, day, "18:00", 2, 0)
        await add_meal(100, date(2024, 3, 12), "12:00", 3, 0)
        await self.click("calendar:day:2024-02-12")
        self.assertEqual(day_buttons(self.keyboard())[day.isoformat()], "12 🟨")
        await add_meal(100, day, "12:00", 4, 0)
        await self.click("calendar:day:2024-02-12")
        self.assertEqual(day_buttons(self.keyboard())[day.isoformat()], "12 🟨")
        await add_meal(100, day, "18:00", 5, 0)
        await self.click("calendar:day:2024-02-12")
        self.assertEqual(day_buttons(self.keyboard())[day.isoformat()], "12 ✅")
        self.assertEqual(await get_meal_counts(100, date(2024, 2, 1), date(2024, 2, 29)), {day.isoformat(): 2})
        with patch("Handlers.day.today_for_user", return_value=day):
            await self.command("/makenote")
        self.assertIn("— ✅", self.screen_text())
        await self.click("statistics:month:2024-02-01")
        self.assertIn("✅ Excellent days: 1", self.screen_text())
        self.assertIn("🍽 Meal notes: 2", self.screen_text())
        self.assertEqual(await self.read_entry(), saved_entry)

    async def test_missing_and_legacy_ratings_are_excluded_from_low_rating_counts(self):
        await save_day_answer(100, date(2024, 2, 12), "mood_control", 6, "ache")
        await save_day_answer(100, date(2024, 2, 13), "sleep_satisfaction", 6, "mood_control")
        await save_day_answer(100, date(2024, 2, 14), "sleep_satisfaction", 7, "mood_control")
        await save_day_answer(100, date(2024, 2, 14), "mood_control", 7, "ache")
        await database.save_ratings(100, date(2024, 2, 15), 1, 1, 1)
        await save_day_answer(200, date(2024, 2, 12), "sleep_satisfaction", 1, "mood_control")
        await self.click("statistics:month:2024-02-01")
        self.assertIn("Average sleep satisfaction: 6.50/10 (1 below 7)", self.screen_text())
        self.assertIn("Average mood stability: 6.50/10 (1 below 7)", self.screen_text())
        self.assertNotIn("Completed days:", self.screen_text())
        self.assertNotIn("Drafts:", self.screen_text())
        await self.click("statistics:month:2024-03-01")
        self.assertIn("Average sleep satisfaction: No data yet (0 below 7)", self.screen_text())
        self.assertIn("Average mood stability: No data yet (0 below 7)", self.screen_text())

    async def test_missing_values_are_underscores_and_meal_comments_do_not_become_html(self):
        comment = "<b>Rice & soup</b>"
        await add_meal(100, date(2024, 2, 12), "12:00", 1, 0, comment)
        await self.click("calendar:day:2024-02-12")
        self.assertIn("Sleep time: ___ – ___", self.screen_text())
        self.assertIn("Sleep satisfaction: ___", self.screen_text())
        self.assertIn("Mood stability: ___", self.screen_text())
        self.assertIn("Stomach pain: ___", self.screen_text())
        self.assertIn(comment, self.screen_text())
        screen = self.screens[self.current_message_id]
        self.assertEqual(screen["parse_mode"], "HTML")
        self.assertIn("<b>February 2024</b>", screen["text"])
        self.assertIn("&lt;b&gt;Rice &amp; soup&lt;/b&gt;", screen["text"])


if __name__ == "__main__":
    unittest.main()
