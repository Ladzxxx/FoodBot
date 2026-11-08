import unittest
from datetime import date
from pathlib import Path

import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove

import database
from Forms.privacy import PrivacySetup
from helpers import BotTests
from localization import t
from privacy_storage import accept_consent, has_consent


class ProfileTests(BotTests):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("DELETE FROM user_profiles")
            await db.execute("DELETE FROM user_consents")
            await db.commit()

    async def reach_timezone(self, language="en"):
        await self.start_with_consent(language)
        await self.command("Foodie fan")

    async def finish_setup(self, period="morning", hour=9, offset=3):
        await self.reach_timezone()
        await self.click(f"profile:utc_offset:{offset}")
        await self.click(f"profile:reminder_period:{period}")
        await self.click(f"profile:reminder_hour:{hour}")

    async def test_new_start_shows_welcome_and_language(self):
        await self.command("/start")
        welcome = self.screens[self.message_events[0][1]]
        menu = welcome["keyboard"]
        self.assertIsInstance(menu, ReplyKeyboardRemove)
        self.assertEqual(welcome["text"], t("en", "privacy.welcome"))
        self.assertIn("Choose your language", self.screen_text())
        self.assertEqual([b.text for b in self.keyboard().inline_keyboard[0]], ["Русский", "English"])
        self.assertIsNone(await database.get_user_profile(100))
        self.assertFalse(await has_consent(100))
        await self.agree_privacy()
        self.assertIsNone(self.keyboard())
        menus = [s["keyboard"] for s in self.screens.values() if isinstance(s["keyboard"], ReplyKeyboardMarkup)]
        self.assertEqual([b.text for row in menus[-1].keyboard for b in row], ["/meal", "/callendar", "/settings"])

    async def test_all_setup_answers_are_saved(self):
        await self.finish_setup()
        profile = await database.get_user_profile(100)
        for field, expected in {
            "language": "en", "nickname": "Foodie fan", "gender": None,
            "birth_year": None, "utc_offset": 3, "reminder_period": "morning",
            "reminder_hour": 9, "setup_complete": 1,
        }.items():
            self.assertEqual(profile[field], expected)
        self.assertIn("Reminders start", self.screen_text())
        self.assertIn("after 9:00 AM", self.screen_text())
        self.assertIsNotNone(profile["reminder_started_at"])
        await self.click(self.button_data("Calendar"))
        self.assertNotIn("Selected day:", self.screen_text())
        self.assertIn("Select a day", self.screen_text())

    async def test_language_is_saved_and_switches_the_interface(self):
        await self.command("/start")
        await self.click(self.button_data("Русский"))
        self.assertIsNone(await database.get_user_profile(100))
        self.assertEqual(await self.state.get_state(), PrivacySetup.consent.state)
        await self.click(self.button_data(t("ru", "privacy.agree")))
        self.assertEqual((await database.get_user_profile(100))["language"], "ru")
        self.assertIn("Введите никнейм", self.screen_text())

    async def test_gender_keyboard_is_reserved_for_future_use(self):
        from Keyboards.profile import profile_keyboard
        keyboard = profile_keyboard('gender', {}, lang='en')
        self.assertEqual([[b.text for b in row] for row in keyboard.inline_keyboard], [
            ["Male"], ["Female"], ["Secret"],
        ])

    async def test_incomplete_old_profile_skips_disabled_questions_after_restart(self):
        await database.ensure_user_profile(100, 100)
        await database.save_profile_answer(100, 'language', 'en')
        await database.save_profile_answer(100, 'nickname', 'Returning user')
        await accept_consent(100, 'en')
        await database.init_db()
        await self.state.clear()
        await self.command('/start')
        self.assertIn('time zone', self.screen_text())
        self.assertEqual(Path(self.screens[self.current_message_id]['photo'].path).name, 'timezones.png')
        await self.click('profile:gender:female')
        self.assertTrue(self.acknowledge.call_args.kwargs['show_alert'])
        profile = await database.get_user_profile(100)
        self.assertIsNone(profile['gender'])
        self.assertIsNone(profile['birth_year'])

    async def test_timezone_grid_has_24_unique_offsets_and_moscow(self):
        await self.reach_timezone()
        rows = self.keyboard().inline_keyboard
        self.assertEqual([len(row) for row in rows], [4, 4, 4, 4, 4, 4, 1])
        offsets = [int(b.callback_data.rsplit(":", 1)[1]) for row in rows[:6] for b in row]
        self.assertEqual(offsets, list(range(3, 13)) + list(range(-1, -12, -1)) + [0, 1, 2])
        self.assertEqual(len(set(offsets)), 24)
        self.assertIn("Moscow", rows[-1][0].text)
        await self.click(rows[-1][0].callback_data)
        self.assertEqual((await database.get_user_profile(100))["utc_offset"], 3)

    async def test_morning_and_evening_hours_with_back(self):
        await self.reach_timezone()
        await self.click("profile:utc_offset:3")
        await self.click("profile:reminder_period:morning")
        self.assertEqual([b.text for b in self.keyboard().inline_keyboard[0]], [
            "6 🕕", "7 🕖", "8 🕗", "9 🕘", "10 🕙", "11 🕚",
        ])
        await self.click(self.button_data("Back"))
        profile = await database.get_user_profile(100)
        self.assertIsNone(profile["reminder_period"])
        self.assertIsNone(profile["reminder_hour"])
        self.assertEqual(profile["nickname"], "Foodie fan")
        await self.click("profile:reminder_period:evening")
        self.assertEqual([b.text for b in self.keyboard().inline_keyboard[0]], [
            "18 🕕", "19 🕖", "20 🕗", "21 🕘", "22 🕙", "23 🕚",
        ])
        await self.click("profile:reminder_hour:9")
        self.assertTrue(self.acknowledge.call_args.kwargs["show_alert"])
        self.assertIsNone((await database.get_user_profile(100))["reminder_hour"])
        await self.click("profile:reminder_hour:21")
        self.assertIn("after 9:00 PM", self.screen_text())

    async def test_setup_resumes_after_restart_without_losing_answers(self):
        await self.start_with_consent("ru")
        await database.init_db()
        await self.state.clear()
        await self.command("/start")
        self.assertNotIn("Hi, I'm Foodie!", self.screen_text())
        self.assertIn("никнейм", self.screen_text())
        await self.command("Restarted")
        profile = await database.get_user_profile(100)
        self.assertEqual(profile["language"], "ru")
        self.assertEqual(profile["nickname"], "Restarted")

    async def test_input_validation_and_stale_buttons_preserve_profile(self):
        await self.command("/start")
        draft = await self.state.get_data()
        await self.click(f"privacy:lang:{draft['privacy_token']}:fr")
        self.assertIsNone(await database.get_user_profile(100))
        self.assertTrue(self.acknowledge.call_args.kwargs['show_alert'])
        await self.agree_privacy()
        await self.command("   ")
        self.assertIsNone((await database.get_user_profile(100))["nickname"])
        await self.command("Nick")
        await self.click("profile:language:ru")
        self.assertEqual((await database.get_user_profile(100))["language"], "en")
        await self.click("profile:gender:male")
        self.assertTrue(self.acknowledge.call_args.kwargs['show_alert'])
        self.assertIsNone((await database.get_user_profile(100))['gender'])
        for value in ("not a year", "1899", str(date.today().year + 1)):
            await self.command(value)
            self.assertIsNone((await database.get_user_profile(100))["birth_year"])
        await self.command("2000")
        await self.click("profile:utc_offset:99")
        self.assertIsNone((await database.get_user_profile(100))["utc_offset"])

    async def test_completed_start_preserves_profile_and_old_diary(self):
        await database.save_ratings(100, date(2024, 2, 12), 5, 6, 4)
        await self.finish_setup()
        before = await database.get_user_profile(100)
        photo_count = self.photo.call_count
        await self.command("/start")
        self.assertEqual(self.photo.call_count, photo_count)
        self.assertNotIn("Selected day:", self.screen_text())
        self.assertIn("Select a day", self.screen_text())
        self.assertEqual(await database.get_user_profile(100), before)
        self.assertEqual(await self.read_day(), {"sleep": 5, "food": 6, "mood": 4})
        self.assertEqual(await database.get_legacy_answer(100, date(2024, 2, 10)), 1)
        await self.click("profile:language:ru")
        self.assertEqual((await database.get_user_profile(100))["language"], "en")

    async def test_new_calendar_command_requests_setup(self):
        await self.command("/callendar")
        self.assertIn("/start", self.screen_text())
        self.assertIsNone(await database.get_user_profile(100))

    async def test_profiles_are_separate_for_each_user(self):
        await self.start_with_consent("ru", user_id=100)
        await self.start_with_consent("en", user_id=200)
        await self.command("First", user_id=100)
        await self.command("Second", user_id=200)
        self.assertEqual((await database.get_user_profile(100))["nickname"], "First")
        self.assertEqual((await database.get_user_profile(200))["nickname"], "Second")
        self.assertEqual((await database.get_user_profile(100))["language"], "ru")

    async def test_every_setup_answer_has_a_confirmation_before_the_next_question(self):
        await self.start_with_consent()
        for answer, expected, is_button, next_image in (
            ("Nick", "Nick", False, "timezones.png"),
            ("profile:utc_offset:3", "+3:00 UTC", True, None),
            ("profile:reminder_period:morning", "Every morning", True, None),
            ("profile:reminder_hour:9", "9:00 AM", True, "seeyousoon.png"),
        ):
            before = len(self.message_events)
            if is_button:
                await self.click(answer)
            else:
                await self.command(answer)
            texts = [self.screens[number]["text"] for event, number in self.message_events[before:] if event == "send"]
            self.assertEqual(len(texts), 2)
            self.assertEqual(texts[0], f"Wrote the answer\n{expected}")
            self.assertNotIn("Wrote the answer", texts[1])
            image = self.screens[self.current_message_id].get("photo")
            if next_image is None:
                self.assertIsNone(image)
            else:
                image_path = Path(image.path)
                self.assertTrue(image_path.is_absolute())
                self.assertTrue(image_path.is_file())
                self.assertEqual(image_path.name, next_image)
                self.assertLessEqual(len(texts[1].encode("utf-16-le")) // 2, 1024)
        self.assertIn("Reminders start", self.screen_text())

    async def test_back_and_invalid_answers_do_not_send_recorded_confirmation(self):
        await self.reach_timezone()
        before = len(self.message_events)
        await self.click("profile:utc_offset:99")
        self.assertEqual(len(self.message_events), before)
        await self.click("profile:utc_offset:3")
        await self.click("profile:reminder_period:morning")
        before = len(self.message_events)
        await self.click(self.button_data("Back"))
        texts = [self.screens[number]["text"] for event, number in self.message_events[before:] if event == "send"]
        self.assertEqual(len(texts), 1)
        self.assertNotIn("Wrote the answer", texts[0])


if __name__ == "__main__":
    unittest.main()
