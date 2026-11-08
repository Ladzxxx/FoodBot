import sqlite3
import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch

import aiosqlite

import database
from day_storage import add_meal, get_meals, update_meal_comment
from Forms.meal import MealNote
from helpers import BotTests
from privacy_storage import accept_consent


class MealTests(BotTests):
    async def set_offset(self, offset):
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("UPDATE user_profiles SET utc_offset = ? WHERE user_id = 100", (offset,))
            await db.commit()

    async def test_meal_uses_local_time_and_keeps_command_date_while_commenting(self):
        await self.set_offset(3)
        now = datetime(2026, 10, 31, 21, 15, tzinfo=timezone.utc)
        with patch("Handlers.meal.datetime") as clock:
            clock.now.return_value = now
            await self.command("/meal")
        self.assertEqual(await self.state.get_state(), MealNote.comment.state)
        meal = (await get_meals(100))[0]
        self.assertEqual(meal["entry_date"], "2026-11-01")
        self.assertEqual(meal["meal_time"], "00:15")
        self.assertEqual(meal["created_at"], int(now.timestamp()))
        self.assertEqual(meal["comment"], "")
        await self.command("Rice and\n vegetables")
        meal = (await get_meals(100))[0]
        self.assertEqual(meal["comment"], "Rice and vegetables")
        self.assertEqual(meal["meal_time"], "00:15")
        self.assertEqual(meal["entry_date"], "2026-11-01")

    async def test_shortcut_comment_and_selected_day_meal_list(self):
        now = datetime(2024, 2, 12, 12, 5, tzinfo=timezone.utc)
        with patch("Handlers.meal.datetime") as clock:
            clock.now.return_value = now
            await self.command("/meal Lunch")
            clock.now.return_value = now.replace(hour=18, minute=30)
            await self.command("/meal Soup")
        await self.click("calendar:day:2024-02-12")
        self.assertIn("\n\nMeals:\nMeal 1 - 12:05 - Lunch\nMeal 2 - 18:30 - Soup", self.screen_text())
        self.assertIn("Sleep time: ___", self.screen_text())
        self.assertIsNone(await self.read_entry())

    async def test_comment_limit_and_skip(self):
        await self.command("/meal")
        prompt = await self.state.get_data()
        await self.command("x" * 51)
        self.assertEqual((await get_meals(100))[0]["comment"], "")
        self.assertEqual(await self.state.get_state(), MealNote.comment.state)
        await self.command("x" * 50)
        self.assertEqual((await get_meals(100))[0]["comment"], "x" * 50)
        await self.click(f"meal:skip:{prompt['meal_id']}", message_id=prompt["message_id"])
        self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
        await self.command("/meal")
        await self.click(self.button_data("Skip"))
        self.assertEqual(len(await get_meals(100)), 2)
        self.assertIsNone(await self.state.get_state())

    async def test_leaving_meal_keeps_the_meal_and_diary_draft(self):
        await self.open_day_edit()
        await self.click(self.button_data("21:00"))
        await self.command("/meal")
        await self.command("/start")
        self.assertEqual(len(await get_meals(100)), 1)
        self.assertEqual((await self.read_entry())["bedtime"], "21:00")
        self.assertIsNone((await database.get_user_profile(100))["last_entry_at"])

    async def test_meals_survive_reinitialization_and_are_private(self):
        await self.command("/meal Test meal")
        await database.init_db()
        meals = await get_meals(100)
        self.assertEqual(meals[0]["comment"], "Test meal")
        self.assertEqual(await get_meals(200), [])
        await update_meal_comment(200, meals[0]["id"], "Wrong user")
        self.assertEqual((await get_meals(100))[0]["comment"], "Test meal")
        with self.assertRaises(sqlite3.IntegrityError):
            await update_meal_comment(100, meals[0]["id"], "x" * 51)

    async def test_negative_offset_and_timezone_changes_do_not_move_old_meals(self):
        await self.set_offset(-11)
        with patch("Handlers.meal.datetime") as clock:
            clock.now.return_value = datetime(2026, 11, 1, 2, tzinfo=timezone.utc)
            await self.command("/meal Breakfast")
        before = (await get_meals(100))[0]
        self.assertEqual(before["entry_date"], "2026-10-31")
        self.assertEqual(before["meal_time"], "15:00")
        await self.command("/timezone")
        await self.click("profile:utc_offset:12")
        self.assertEqual((await get_meals(100))[0], before)

    async def test_many_meals_are_paged_without_losing_descriptions(self):
        for index in range(23):
            await add_meal(100, date(2024, 2, 12), "12:00", index, 0, f"Meal {index}")
        await self.click("calendar:day:2024-02-12")
        self.assertIn("Meal 10 -", self.screen_text())
        self.assertNotIn("Meal 11 -", self.screen_text())
        await self.click(self.button_data("Meals →"))
        self.assertIn("Meal 11 -", self.screen_text())
        await self.click(self.button_data("Meals →"))
        self.assertIn("Meal 23 -", self.screen_text())
        self.assertLess(len(self.screen_text()), 4096)
        self.assertIsNotNone(self.button_data("Edit the day"))

    async def test_meals_appear_in_statistics_without_completing_a_day(self):
        with patch("Handlers.meal.datetime") as clock:
            clock.now.return_value = datetime(2024, 2, 12, 12, tzinfo=timezone.utc)
            await self.command("/meal Lunch")
        await self.command("/statistics")
        self.assertIn("🍽 Meal notes: 1", self.screen_text())
        self.assertIn("✅ Excellent days: 0", self.screen_text())
        self.assertIsNone((await database.get_user_profile(100))["last_entry_at"])

    async def test_command_accepts_explicit_time_and_description(self):
        await self.set_offset(3)
        with patch('Handlers.meal.datetime') as clock:
            clock.now.return_value = datetime(2026, 10, 31, 22, tzinfo=timezone.utc)
            await self.command('/meal 13:45 Soup')
        meal = (await get_meals(100))[0]
        self.assertEqual((meal['entry_date'], meal['meal_time'], meal['comment']),
            ('2026-11-01', '13:45', 'Soup'))
        self.assertIsNone(await self.state.get_state())

    async def test_typed_time_updates_the_same_pending_meal(self):
        await self.command('/meal')
        original = (await get_meals(100))[0]
        await self.command('13:45')
        pending = (await get_meals(100))[0]
        self.assertEqual(pending, {**original, 'meal_time': '13:45'})
        self.assertEqual(await self.state.get_state(), MealNote.comment.state)
        await self.command('14:00 Rice')
        self.assertEqual(await get_meals(100), [{**original, 'meal_time': '14:00', 'comment': 'Rice'}])
        self.assertIsNone(await self.state.get_state())

    async def test_time_edit_after_midnight_and_timezone_change_keeps_record_and_timer(self):
        await self.set_offset(3)
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute('UPDATE user_profiles SET last_entry_at = 123456 WHERE user_id = 100')
            await db.commit()
        with patch('Handlers.meal.datetime') as clock:
            clock.now.return_value = datetime(2026, 10, 31, 22, tzinfo=timezone.utc)
            await self.command('/meal 13:45 Soup')
        original = (await get_meals(100))[0]
        await self.command('/timezone')
        await self.click('profile:utc_offset:-11')
        await self.click(f"meal:time:{original['id']}")
        with patch('Handlers.meal.datetime') as clock:
            clock.now.return_value = datetime(2026, 11, 2, 3, tzinfo=timezone.utc)
            await self.command('23:59')
        self.assertEqual(await get_meals(100), [{**original, 'meal_time': '23:59'}])
        self.assertIn('13:45', self.screen_text())
        self.assertIn('23:59', self.screen_text())
        self.assertEqual((await database.get_user_profile(100))['last_entry_at'], 123456)

    async def test_invalid_time_in_command_or_edit_does_not_change_records(self):
        for value in ('24:00', '12:60', '9:00'):
            with self.subTest(command=value):
                await self.command('/meal ' + value + ' Soup')
                self.assertEqual(await get_meals(100), [])
        await self.command('/meal 12:00 Soup')
        original = (await get_meals(100))[0]
        await self.click(f"meal:time:{original['id']}")
        for value in ('24:00', '12:60', '9:00', 'invalid'):
            with self.subTest(edit=value):
                await self.command(value)
                self.assertEqual(await get_meals(100), [original])
                self.assertEqual(await self.state.get_state(), MealNote.time.state)

    async def test_cancelling_time_edit_returns_to_comment_or_saved_meal(self):
        await self.command('/meal')
        original = (await get_meals(100))[0]
        await self.click(f"meal:time:{original['id']}")
        await self.click(self.button_data('Cancel'))
        self.assertEqual(await self.state.get_state(), MealNote.comment.state)
        self.assertEqual(await get_meals(100), [original])
        await self.command('Soup')
        saved = (await get_meals(100))[0]
        await self.click(f"meal:time:{original['id']}")
        cancel = self.button_data('Cancel')
        question = self.current_message_id
        await self.click(cancel)
        self.assertIsNone(await self.state.get_state())
        self.assertEqual(await get_meals(100), [saved])
        await self.click(cancel, message_id=question)
        self.assertTrue(self.acknowledge.call_args.kwargs['show_alert'])
        self.assertEqual(await get_meals(100), [saved])

    async def test_other_user_cannot_edit_meal_time(self):
        await self.command('/meal 12:00 Soup')
        original = (await get_meals(100))[0]
        await database.ensure_user_profile(200, 200)
        await accept_consent(200, 'en')
        await self.click(f"meal:time:{original['id']}", user_id=200)
        self.assertTrue(self.acknowledge.call_args.kwargs['show_alert'])
        self.assertEqual(await get_meals(100), [original])
        self.assertEqual(await get_meals(200), [])


if __name__ == "__main__":
    unittest.main()
