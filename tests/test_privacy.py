from datetime import date
from unittest.mock import patch

import aiosqlite

import database
from day_storage import add_meal, add_medication, get_day_entry, save_day_answer
from Forms.day import DayEdit
from Forms.privacy import PrivacySetup
from helpers import BotTests
from localization import t
from morning_storage import start_morning_session
from privacy_storage import (
    CONSENT_VERSION, POLICY_VERSION, USER_TABLES, accept_consent, has_consent,
    pending_deletions,
)


class PrivacyTests(BotTests):
    async def remove_consent(self):
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("DELETE FROM user_consents WHERE user_id = 100")
            await db.commit()

    async def test_new_user_profile_is_created_only_after_explicit_consent(self):
        await self.command('/start', user_id=200, first_name='Vlad')
        self.assertIsNone(await database.get_user_profile(200))
        await self.click(self.button_data('Русский'), user_id=200)
        self.assertIsNone(await database.get_user_profile(200))
        self.assertFalse(await has_consent(200))
        self.assertIn(t('ru', 'privacy.consent'), self.screen_text())
        with patch('privacy_storage.time', return_value=1234567890):
            await self.click(self.button_data(t('ru', 'privacy.agree')), user_id=200)
        profile = await database.get_user_profile(200)
        self.assertEqual(profile['language'], 'ru')
        self.assertEqual(profile['setup_complete'], 0)
        self.assertIn('Введите никнейм', self.screen_text())
        async with aiosqlite.connect(database.DB_PATH) as db:
            rows = await db.execute_fetchall('SELECT policy_version, consent_version, accepted_at, language FROM user_consents WHERE user_id = 200')
        self.assertEqual(rows, [(POLICY_VERSION, CONSENT_VERSION, 1234567890, 'ru')])

    async def test_existing_user_is_blocked_until_consent_and_keeps_saved_answers(self):
        day = date(2024, 2, 12)
        await save_day_answer(100, day, 'bedtime', '22:00', 'wake_time')
        before_entry = await get_day_entry(100, day)
        before_profile = await database.get_user_profile(100)
        await self.remove_consent()
        await self.command('/meal Lunch')
        consent_message = self.current_message_id
        agree = self.button_data('Agree')
        for command in ('/statistics', '/settings', '/language'):
            await self.command(command)
            self.assertEqual(await self.state.get_state(), PrivacySetup.consent.state)
            self.assertEqual(await get_day_entry(100, day), before_entry)
            self.assertEqual(await database.get_user_profile(100), before_profile)
        await self.click('day:edit:2024-02-12')
        self.assertTrue(self.acknowledge.call_args.kwargs['show_alert'])
        self.assertEqual(await get_day_entry(100, day), before_entry)
        await self.click(agree, message_id=consent_message)
        self.assertTrue(await has_consent(100))
        self.assertEqual(await get_day_entry(100, day), before_entry)
        self.assertEqual(await database.get_legacy_answer(100, date(2024, 2, 10)), 1)
        self.assertEqual(await database.get_user_profile(100), before_profile)
        self.assertIn('Select a day', self.screen_text())

    async def test_expired_consent_requires_a_new_decision(self):
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("UPDATE user_consents SET policy_version = 'old' WHERE user_id = 100")
            await db.commit()
        self.assertFalse(await has_consent(100))
        self.assertEqual(await database.get_reminder_profiles(), [])
        await self.command('/start')
        self.assertEqual(await self.state.get_state(), PrivacySetup.language.state)
        await self.agree_privacy()
        self.assertTrue(await has_consent(100))

    async def test_stale_foreign_and_wrong_message_buttons_cannot_save_consent(self):
        await self.command('/start', user_id=200)
        await self.click(self.button_data('English'), user_id=200)
        agree = self.button_data('Agree')
        decline = self.button_data("Don't agree")
        message_id = self.current_message_id
        await self.click(agree, user_id=300, message_id=message_id)
        self.assertFalse(await has_consent(300))
        await self.click(agree, user_id=200, message_id=message_id + 1)
        self.assertFalse(await has_consent(200))
        self.assertTrue(self.acknowledge.call_args.kwargs['show_alert'])
        await self.click(agree, user_id=200, message_id=message_id)
        profile = await database.get_user_profile(200)
        await self.click(decline, user_id=200, message_id=message_id)
        self.assertTrue(self.acknowledge.call_args.kwargs['show_alert'])
        self.assertTrue(await has_consent(200))
        self.assertEqual(await database.get_user_profile(200), profile)

    async def test_whitespace_in_settings_is_rejected_without_losing_progress(self):
        await self.command('/settings')
        await self.click('profile:language:en')
        before = await self.state.get_data()
        profile = await database.get_user_profile(100)
        for text in ('', '   ', '\t\n', '\u00a0'):
            with self.subTest(text=repr(text)):
                await self.command(text)
                self.assertEqual(await self.state.get_data(), before)
                self.assertEqual(await database.get_user_profile(100), profile)
                self.assertIn('nickname', self.screen_text())

    async def test_whitespace_without_consent_does_not_crash_or_write_answers(self):
        await self.remove_consent()
        profile = await database.get_user_profile(100)
        for text in ('   ', '\t\n', '\u00a0'):
            await self.command(text)
            self.assertFalse(await has_consent(100))
            self.assertEqual(await database.get_user_profile(100), profile)
            self.assertIsNone(await self.read_entry())
        self.assertEqual(await self.state.get_state(), PrivacySetup.consent.state)

    async def test_policy_is_available_without_profile_and_keeps_pending_consent(self):
        await self.command('/privacy', user_id=200)
        self.assertIn('/delete_me', self.screen_text())
        self.assertIsNone(await database.get_user_profile(200))
        await self.remove_consent()
        await self.command('/start')
        await self.click(self.button_data('English'))
        before = await self.state.get_data()
        await self.command('/privacy')
        self.assertEqual(await self.state.get_data(), before)
        self.assertEqual(await self.state.get_state(), PrivacySetup.consent.state)

    async def test_cancelling_deletion_preserves_active_diary_and_consent(self):
        await self.open_day_edit()
        await self.click(self.button_data('22:00'))
        entry = await self.read_entry()
        before = await self.state.get_data()
        await self.command('/delete_me')
        self.assertEqual(await self.read_entry(), entry)
        self.assertTrue(await has_consent(100))
        await self.click(self.button_data(t('en', 'common.cancel')))
        self.assertEqual(await self.state.get_state(), DayEdit.answer.state)
        after = await self.state.get_data()
        self.assertEqual({key: after[key] for key in before}, before)
        self.assertEqual(await self.read_entry(), entry)
        self.assertTrue(await has_consent(100))

    async def seed_all_user_tables(self, user_id):
        day = date(2024, 2, 12)
        await database.ensure_user_profile(user_id, user_id)
        await accept_consent(user_id, 'en')
        await database.save_ratings(user_id, day, 4, 5, 6)
        await save_day_answer(user_id, day, 'bedtime', '22:00', 'wake_time')
        await add_medication(user_id, day, 'Test medicine', False)
        await add_meal(user_id, day, '12:00', 1, 0, 'Soup')
        await start_morning_session(user_id, day, 'continue', 0)
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute('INSERT INTO calendar_answers VALUES (?, ?, 1)', (user_id, day.isoformat()))
            await db.execute("INSERT INTO day_pain_answers VALUES (?, ?, 'pain_location', 'in_progress', 1)", (user_id, day.isoformat()))
            await db.execute("INSERT INTO day_pain_options VALUES (?, ?, 'pain_location', 'upper_right', NULL, 1, 1)", (user_id, day.isoformat()))
            await db.commit()

    async def test_confirmed_deletion_clears_all_ten_tables_only_for_owner(self):
        await self.seed_all_user_tables(100)
        await self.seed_all_user_tables(200)
        await self.command('/delete_me')
        await self.click(self.button_data('Delete my data'))
        self.assertEqual(self.screen_text(), t('en', 'privacy.deleted'))
        self.assertIsNone(await self.state.get_state())
        self.assertFalse(await has_consent(100))
        self.assertNotIn(100, pending_deletions)
        async with aiosqlite.connect(database.DB_PATH) as db:
            for table in USER_TABLES:
                with self.subTest(table=table):
                    owner = await db.execute_fetchall(f'SELECT COUNT(*) FROM {table} WHERE user_id = 100')
                    other = await db.execute_fetchall(f'SELECT COUNT(*) FROM {table} WHERE user_id = 200')
                    self.assertEqual(owner[0][0], 0)
                    self.assertGreater(other[0][0], 0)

    async def test_decline_deletes_old_answers_and_allows_a_fresh_start(self):
        await database.ensure_user_profile(200, 200)
        await self.remove_consent()
        await self.command('/start')
        await self.click(self.button_data('English'))
        await self.click(self.button_data("Don't agree"))
        self.assertEqual(self.screen_text(), t('en', 'privacy.declined'))
        self.assertIsNone(await database.get_user_profile(100))
        self.assertIsNone(await database.get_legacy_answer(100, date(2024, 2, 10)))
        self.assertIsNotNone(await database.get_user_profile(200))
        await self.command('some text')
        self.assertIsNone(await database.get_user_profile(100))
        await self.command('/start')
        self.assertEqual(await self.state.get_state(), PrivacySetup.language.state)

    async def test_failed_deletion_revokes_access_and_can_be_retried(self):
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute('CREATE TABLE future_user_data (user_id INTEGER)')
            await db.execute('INSERT INTO future_user_data VALUES (100)')
            await db.commit()
        await self.command('/delete_me')
        with self.assertLogs('Handlers.privacy', level='ERROR'):
            await self.click(self.button_data('Delete my data'))
        self.assertEqual(self.screen_text(), t('en', 'privacy.delete_failed'))
        self.assertFalse(await has_consent(100))
        self.assertEqual((await database.get_user_profile(100))['reminders_enabled'], 0)
        self.assertEqual(await database.get_reminder_profiles(), [])
        await self.command('/start')
        self.assertEqual(self.screen_text(), t('en', 'privacy.delete_failed'))
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute('DROP TABLE future_user_data')
            await db.commit()
        await self.command('/delete_me')
        await self.click(self.button_data('Delete my data'))
        self.assertIsNone(await database.get_user_profile(100))
        self.assertNotIn(100, pending_deletions)
