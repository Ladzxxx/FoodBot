import asyncio
import sqlite3
import unittest
from datetime import date

import aiosqlite
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import EditMessageText

import database
from day_storage import get_medications, save_day_answer
from Forms.day import DayEdit, day_marker, sleep_minutes
from Handlers.day import parse_bedtime, parse_button_answer, question_text
from Handlers.statistics import summary_text
from helpers import BotTests


class DayTests(BotTests):
    async def test_day_comment_limit_and_escaped_calendar_text(self):
        await self.main_answers()
        await self.click(self.button_data('Yes'))
        await self.command('x' * 201)
        self.assertIsNone((await self.read_entry())['day_comment'])
        note = '<b>' + 'x' * 193 + '</b>'
        self.assertEqual(len(note), 200)
        await self.command(note)
        self.assertEqual((await self.read_entry())['day_comment'], note)
        await self.click('calendar:day:2024-02-12')
        self.assertIn('&lt;b&gt;', self.screens[self.current_message_id]['text'])
        self.assertIn(note, self.screen_text())

    async def main_answers(self, ache="No", day="2024-02-12"):
        await self.click(f"day:edit:{day}")
        for label in ("21:00", "08:00", "8", "7", ache):
            await self.click(self.button_data(label))

    async def pain_without_medicine(self):
        await self.main_answers(ache="Yes")
        await self.click(self.button_data("6"))
        await self.click(self.button_data("No"))

    async def test_time_buttons_and_typed_minutes_save_immediately(self):
        await self.click("day:edit:2024-02-12")
        self.assertIn("When did you go to bed?", self.screen_text())
        question_id = self.current_message_id
        self.assertEqual(len(self.keyboard().inline_keyboard), 10)
        await self.command("21:37")
        entry = await self.read_entry()
        self.assertEqual(entry["bedtime"], "21:37")
        self.assertEqual(entry["next_step"], "wake_time")
        self.assertEqual(entry["completed"], 0)
        self.assertIsNone((await database.get_user_profile(100))["last_entry_at"])
        recorded = self.screens[question_id]
        self.assertIn("When did you go to bed?", recorded["text"])
        self.assertIn("Answer recorded\n21:37", recorded["text"])
        self.assertIsNone(recorded["keyboard"])
        await self.command("7:05")
        self.assertEqual((await self.read_entry())["wake_time"], "07:05")
        self.assertEqual([b.text for row in self.keyboard().inline_keyboard[:-1] for b in row], [str(n) for n in range(1, 11)])

    async def test_no_pain_no_comment_completes_entry(self):
        await self.main_answers()
        question_id = self.current_message_id
        await self.click(self.button_data("No"))
        self.assertTrue(self.screen_text().startswith("Entry saved!"))
        self.assertIn("Sleep time: 21:00 – 08:00", self.screen_text())
        self.assertIn("Sleep satisfaction: 8/10", self.screen_text())
        self.assertIn("Mood stability: 7/10", self.screen_text())
        self.assertIn("Stomach pain: No", self.screen_text())
        self.assertIn("Answer recorded\nNo", self.screens[question_id]["text"])
        entry = await self.read_entry()
        self.assertEqual(entry["completed"], 1)
        self.assertEqual(entry["day_comment"], "")
        self.assertIsNone(entry["pain_intensity"])
        self.assertIsNotNone((await database.get_user_profile(100))["last_entry_at"])
        self.assertIsNone(await self.state.get_state())
        await self.click(self.button_data("Calendar"))
        self.assertNotIn("Selected day:", self.screen_text())

    async def test_day_comment_is_recorded_and_shown_below_meals(self):
        await self.main_answers()
        await self.click(self.button_data("Yes"))
        question_id = self.current_message_id
        await self.command("A short daily note")
        self.assertEqual((await self.read_entry())["day_comment"], "A short daily note")
        self.assertIn("Answer recorded\nA short daily note", self.screens[question_id]["text"])
        await self.click("calendar:day:2024-02-12")
        self.assertIn("A short daily note", self.screen_text())
        self.assertLess(self.screen_text().index('Meals:'), self.screen_text().index('Day comment:'))
        labels = [b.text for row in self.keyboard().inline_keyboard for b in row]
        self.assertNotIn('View full entry', labels)

    async def test_pain_without_painkillers_and_description_skip(self):
        await self.pain_without_medicine()
        self.assertIn("describe what the pain felt like", self.screen_text())
        await self.click(self.button_data("Yes"))
        self.assertIn('Where did you feel the pain?', self.screen_text())
        for _ in range(4):
            await self.click(self.button_data('☐ Skip'))
            await self.click(self.button_data('Done'))
        await self.click(self.button_data("No"))
        self.assertIn('Would you like to add a note about the day?', self.screen_text())
        await self.click(self.button_data("No"))
        entry = await self.read_entry()
        self.assertEqual(entry["ache"], 1)
        self.assertEqual(entry["pain_intensity"], 6)
        self.assertEqual(entry["painkillers"], 0)
        self.assertEqual(entry["pain_description_requested"], 1)
        self.assertEqual(entry["completed"], 1)
        self.assertEqual(await get_medications(100, date(2024, 2, 12)), [])

    async def test_medication_loop_effects_and_both_notes(self):
        await self.main_answers(ache="Yes")
        await self.click(self.button_data("9"))
        await self.click(self.button_data("Yes"))
        await self.command("Medicine A, one tablet")
        medicines = await get_medications(100, date(2024, 2, 12))
        self.assertEqual(medicines[0]["description"], "Medicine A, one tablet")
        self.assertIsNone(medicines[0]["relief"])
        await self.click(self.button_data("A little"))
        await self.click(self.button_data("Yes"))
        await self.command("Medicine B, two tablets")
        await self.click(self.button_data("No"))
        await self.click(self.button_data("No"))
        summaries = [s["text"] for s in self.screens.values() if s["text"].startswith("All recorded medications:")]
        self.assertEqual(len(summaries), 1)
        self.assertIn("Medicine A, one tablet — Helped: A little", summaries[0])
        self.assertIn("Medicine B, two tablets — Helped: No", summaries[0])
        await self.click(self.button_data("No"))
        await self.click(self.button_data("Yes"))
        await self.command("Pain episode note")
        self.assertIn('Would you like to add a note about the day?', self.screen_text())
        await self.click(self.button_data("Yes"))
        await self.command("Daily note")
        entry = await self.read_entry()
        self.assertEqual(entry["day_comment"], "Daily note")
        self.assertEqual(entry["pain_comment"], "Pain episode note")
        self.assertEqual(entry["completed"], 1)
        medicines = await get_medications(100, date(2024, 2, 12))
        self.assertEqual([m["relief"] for m in medicines], ["a_little", "no"])
        await self.click("calendar:day:2024-02-12")
        self.assertIn('Daily note', self.screen_text())
        for hidden in ("Pain episode note", "Medicine A", "Pain intensity:"):
            self.assertNotIn(hidden, self.screen_text())

    async def test_cancelling_keeps_saved_progress_and_reopening_resumes(self):
        await self.click("day:edit:2024-02-12")
        await self.click(self.button_data("22:00"))
        await self.click(self.button_data("Cancel"))
        self.assertNotIn("Selected day:", self.screen_text())
        self.assertEqual((await self.read_entry())["bedtime"], "22:00")
        self.assertEqual((await self.read_entry())["completed"], 0)
        await self.open_day_edit()
        self.assertIn("What time did you wake up today?", self.screen_text())

    async def test_cancel_before_any_answer_creates_no_entry(self):
        await self.click("day:edit:2024-02-12")
        await self.click(self.button_data("Cancel"))
        self.assertIsNone(await self.read_entry())

    async def test_restart_resumes_pending_medication_effect(self):
        await self.main_answers(ache="Yes")
        await self.click(self.button_data("4"))
        await self.click(self.button_data("Yes"))
        await self.command("Medicine A, stated dose")
        stale_button = self.button_data("Yes")
        await self.state.clear()
        await database.init_db()
        await self.click(stale_button)
        self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
        await self.open_day_edit()
        self.assertIn("Did it help?", self.screen_text())
        await self.click(self.button_data("Yes"))
        self.assertEqual((await get_medications(100, date(2024, 2, 12)))[0]["relief"], "yes")

    async def test_completed_entry_can_be_edited_and_partial_edits_are_saved(self):
        await self.finish_edit()
        await self.click("day:edit:2024-02-12")
        await self.click(self.button_data("23:00"))
        await self.click(self.button_data("Cancel"))
        entry = await self.read_entry()
        self.assertEqual(entry["bedtime"], "23:00")
        self.assertEqual(entry["wake_time"], "08:00")
        self.assertEqual(entry["completed"], 0)
        await self.open_day_edit()
        for label in ("09:00", "10", "1", "No", "No"):
            await self.click(self.button_data(label))
        self.assertEqual((await self.read_entry())["completed"], 1)
        self.assertEqual((await self.read_entry())["sleep_satisfaction"], 10)

    async def test_changing_pain_to_no_removes_inapplicable_details(self):
        await self.pain_without_medicine()
        await self.click(self.button_data("No"))
        await self.click(self.button_data("Yes"))
        await self.command("Old pain note")
        await self.click(self.button_data("No"))
        await self.finish_edit()
        entry = await self.read_entry()
        self.assertEqual(entry["ache"], 0)
        self.assertIsNone(entry["pain_intensity"])
        self.assertIsNone(entry["pain_comment"])
        self.assertEqual(await get_medications(100, date(2024, 2, 12)), [])

    async def test_time_and_rating_validation_do_not_save_invalid_values(self):
        await self.click("day:edit:2024-02-12")
        for text in ("24:00", "21:99", "21:3", "not time"):
            await self.command(text)
            self.assertIsNone(await self.read_entry())
        await self.command("21:20")
        await self.command("08:15")
        button = self.button_data("1")
        for value in ("0", "11", "text"):
            await self.click(button.rsplit(":", 1)[0] + ":" + value)
            self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
        self.assertIsNone((await self.read_entry())["sleep_satisfaction"])

    async def test_duplicate_and_stale_buttons_do_not_advance_again(self):
        await self.click("day:edit:2024-02-12")
        button = self.button_data("21:00")
        await asyncio.gather(self.click(button), self.click(button))
        self.assertEqual((await self.state.get_data())["step"], "wake_time")
        self.assertEqual((await self.read_entry())["bedtime"], "21:00")
        current = self.button_data("08:00")
        await self.click(current, user_id=200)
        self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
        await self.click(current, message_id=1)
        self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
        self.assertIsNone((await self.read_entry())["wake_time"])

    async def test_users_and_dates_are_separate(self):
        await self.finish_edit(values=(8, 7), user_id=100)
        await self.finish_edit(values=(2, 3), user_id=200)
        await self.finish_edit(day="2024-03-12", values=(10, 10))
        self.assertEqual((await self.read_entry())["sleep_satisfaction"], 8)
        self.assertEqual((await self.read_entry(user_id=200))["sleep_satisfaction"], 2)
        self.assertEqual((await self.read_entry(day="2024-03-12"))["sleep_satisfaction"], 10)

    async def test_invalid_database_rating_rolls_back_the_answer(self):
        await self.finish_edit()
        before = await self.read_entry()
        with self.assertRaises(sqlite3.IntegrityError):
            await save_day_answer(100, date(2024, 2, 12), "sleep_satisfaction", 11, "mood_control")
        self.assertEqual(await self.read_entry(), before)

    async def test_old_rating_buttons_cannot_write_new_answers(self):
        await self.click("day:rate:old:0:5")
        self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
        self.assertIsNone(await self.read_entry())

    async def test_failed_confirmation_does_not_duplicate_medication(self):
        await self.main_answers(ache="Yes")
        await self.click(self.button_data("5"))
        await self.click(self.button_data("Yes"))
        effect = self.api_edit.side_effect
        self.api_edit.side_effect = TelegramNetworkError(
            method=EditMessageText(chat_id=100, message_id=self.current_message_id, text="test"),
            message="Test confirmation failure",
        )
        with self.assertRaises(TelegramNetworkError):
            await self.command("Medicine A, one tablet")
        self.api_edit.side_effect = effect
        await self.command("Medicine A, one tablet")
        self.assertIn("Did it help?", self.screen_text())
        self.assertEqual(len(await get_medications(100, date(2024, 2, 12))), 1)

    async def test_long_medication_summary_is_split_without_losing_records(self):
        await self.main_answers(ache="Yes")
        await self.click(self.button_data("5"))
        await self.click(self.button_data("Yes"))
        await self.command("Medicine A, stated dose")
        await self.click(self.button_data("Yes"))
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.executemany(
                "INSERT INTO day_medications (user_id, entry_date, description, relief) VALUES (?, ?, ?, ?)",
                [(100, "2024-02-12", f"Medicine {i}: " + "x" * 280, "no") for i in range(20)],
            )
            await db.commit()
        await self.click(self.button_data("No"))
        summaries = [s["text"] for s in self.screens.values() if s["text"].startswith(("All recorded medications:", "Recorded medications (continued):"))]
        self.assertGreater(len(summaries), 1)
        self.assertTrue(all(len(text) < 4096 for text in summaries))
        self.assertIn("Medicine 19:", "\n".join(summaries))


    async def test_time_keyboards_cover_exact_noon_range_and_36_hour_maximum(self):
        await self.open_day_edit()
        buttons = [button for row in self.keyboard().inline_keyboard for button in row]
        choices = [button for button in buttons if ":bedtime:" in button.callback_data]
        self.assertEqual(len(choices), 25)
        self.assertTrue(choices[0].callback_data.endswith(":bedtime:yesterday 12:00"))
        self.assertTrue(choices[-1].callback_data.endswith(":bedtime:today 12:00"))
        self.assertIn("Yesterday (11.02.2024)", [button.text for button in buttons])
        self.assertIn("Today (12.02.2024)", [button.text for button in buttons])
        self.assertTrue(all(len(button.callback_data.encode("utf8")) <= 64 for button in buttons))
        await self.click(choices[0].callback_data)
        self.assertEqual((await self.read_entry())["bedtime_day"], -1)
        wake_buttons = [button.text for row in self.keyboard().inline_keyboard[:-1] for button in row]
        self.assertEqual(wake_buttons, [f"{hour:02d}:00" for hour in range(25)])
        await self.click(self.button_data("24:00"))
        self.assertEqual(sleep_minutes(await self.read_entry()), 36 * 60)
        self.assertEqual((await self.state.get_data())["step"], "sleep_satisfaction")

    async def test_negative_sleep_is_not_saved_and_repeated_bad_answer_is_safe(self):
        await self.open_day_edit()
        await self.command("today 10:30")
        before = await self.read_entry()
        question_id = self.current_message_id
        bad_button = self.button_data("09:00")
        await self.click(bad_button)
        self.assertEqual(await self.read_entry(), before)
        self.assertIn("Sleep duration cannot be negative.", self.screens[question_id]["text"])
        self.assertEqual((await self.state.get_data())["step"], "wake_time")
        original_effect = self.api_edit.side_effect
        self.api_edit.side_effect = TelegramBadRequest(
            method=EditMessageText(chat_id=100, message_id=question_id, text="same error"),
            message="Bad Request: message is not modified",
        )
        await self.click(bad_button)
        self.api_edit.side_effect = original_effect
        self.assertEqual(await self.read_entry(), before)
        await self.command("09:00")
        self.assertEqual(await self.read_entry(), before)
        await self.command("11:00")
        self.assertEqual(sleep_minutes(await self.read_entry()), 30)
        self.assertEqual((await self.state.get_data())["step"], "sleep_satisfaction")

    async def test_after_midnight_bedtime_survives_restart_and_updates_views(self):
        await self.open_day_edit()
        await self.command("03:15")
        self.assertEqual((await self.read_entry())["bedtime_day"], 0)
        await self.state.clear()
        await database.init_db()
        await self.open_day_edit()
        await self.command("07:05")
        for label in ("8", "8", "No", "No"):
            await self.click(self.button_data(label))
        entry = await self.read_entry()
        self.assertEqual(sleep_minutes(entry), 3 * 60 + 50)
        self.assertEqual(day_marker(entry), "🟥")
        await self.click("calendar:day:2024-02-12")
        self.assertIn("Sleep time: 03:15 (Today) – 07:05", self.screen_text())
        await self.click(self.button_data("Statistics"))
        self.assertIn("Average sleep duration: 3 h 50 min", self.screen_text())


class SleepTimeTests(unittest.TestCase):
    def test_only_red_completed_days_with_pain_get_sos_marker(self):
        entry = {'completed': 1, 'bedtime': '23:00', 'wake_time': '03:00',
                 'sleep_satisfaction': 1, 'mood_control': 1, 'ache': 1}
        self.assertEqual(day_marker(entry), '🆘')
        self.assertEqual(day_marker({**entry, 'ache': 0}), '🟥')
        self.assertEqual(day_marker({**entry, 'completed': 0}), '📝')
        good = {**entry, 'bedtime': '21:00', 'wake_time': '08:00', 'sleep_satisfaction': 8, 'mood_control': 8}
        self.assertEqual(day_marker(good, 2), '✅')

    def test_sleep_uses_selected_days_instead_of_wrapping_at_24_hours(self):
        for bedtime, bedtime_day, wake_time, minutes in (
            ("20:00", -1, "21:00", 25 * 60),
            ("22:00", -1, "06:00", 8 * 60),
            ("20:00", -1, "20:00", 24 * 60),
            ("23:45", -1, "07:15", 7 * 60 + 30),
            ("00:00", 0, "06:00", 6 * 60),
            ("12:00", -1, "24:00", 36 * 60),
            ("12:00", 0, "24:00", 12 * 60),
            ("10:00", 0, "09:00", -60),
            ("06:00", 0, "06:00", 0),
        ):
            with self.subTest(bedtime=bedtime, wake_time=wake_time):
                self.assertEqual(sleep_minutes({"bedtime": bedtime, "bedtime_day": bedtime_day, "wake_time": wake_time}), minutes)

    def test_missing_or_invalid_sleep_times_are_excluded(self):
        for entry in ({}, {"bedtime": None, "wake_time": "08:00"}, {"bedtime": "24:00", "wake_time": "08:00"}, {"bedtime": "22:60", "wake_time": "08:00"}, {"bedtime": "22:00", "wake_time": "24:01"}):
            self.assertIsNone(sleep_minutes(entry))

    def test_sleep_statistics_use_the_corrected_duration(self):
        entries = {"2024-02-12": {"completed": 1, "bedtime": "20:00", "wake_time": "21:00"}}
        self.assertIn("Average sleep duration: 25 h 00 min", summary_text(entries, [], []))

    def test_sleep_questions_show_actual_dates_across_month_boundaries(self):
        self.assertIn("Bedtime range: 29.02.2024 12:00 – 01.03.2024 12:00", question_text(date(2024, 3, 1), "bedtime"))
        self.assertIn("Wake-up date: 01.03.2024", question_text(date(2024, 3, 1), "wake_time"))

    def test_bedtime_parser_enforces_noon_to_noon_and_wake_end_of_day(self):
        for text, expected in (
            ("12:00", ("12:00", -1)), ("23:59", ("23:59", -1)),
            ("00:00", ("00:00", 0)), ("today 12:00", ("12:00", 0)),
            ("Yesterday 20:00", ("20:00", -1)), ("Today 11:59", ("11:59", 0)),
        ):
            self.assertEqual(parse_bedtime(text), expected)
        for text in ("yesterday 11:59", "today 12:01", "today 23:00", "24:00"):
            with self.assertRaises(ValueError):
                parse_bedtime(text)
        self.assertEqual(parse_button_answer("wake_time", "24:00"), "24:00")
        with self.assertRaises(ValueError):
            parse_button_answer("wake_time", "24:01")

    def test_negative_sleep_is_excluded_from_statistics(self):
        entries = {"2024-02-12": {"completed": 0, "bedtime": "10:00", "bedtime_day": 0, "wake_time": "09:00"}}
        self.assertIn("Average sleep duration: No data yet", summary_text(entries, [], []))

    def test_after_midnight_bedtime_does_not_meet_the_bedtime_condition(self):
        entry = {"completed": 1, "bedtime": "03:00", "bedtime_day": 0, "wake_time": "13:00", "sleep_satisfaction": 8, "mood_control": 8}
        self.assertEqual(day_marker(entry, 2), "🟨")


if __name__ == "__main__":
    unittest.main()
