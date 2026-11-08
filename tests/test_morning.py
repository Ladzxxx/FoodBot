from datetime import date, timedelta
from unittest.mock import patch

import aiosqlite

import database
from day_storage import get_day_entry, get_medications, save_day_answer
from helpers import BotTests
from morning_storage import get_morning_session, morning_entry_needed
from pain_storage import get_pain_answers


class MorningTests(BotTests):
    today = date(2026, 11, 1)
    yesterday = date(2026, 10, 31)

    async def open_morning(self, action='open', mode=None):
        data = f'morning:{action}:{self.today.isoformat()}'
        if mode:
            data += ':' + mode
        with patch('Handlers.morning.today_for_user', return_value=self.today):
            await self.click(data)

    async def save_sleep(self):
        for label in ('22:00', '08:00', '8'):
            await self.click(self.button_data(label))

    async def test_sleep_and_other_answers_go_to_two_dates_and_timer_changes_at_end(self):
        await self.open_morning()
        await self.save_sleep()
        sleep = await get_day_entry(100, self.today)
        self.assertEqual(sleep['bedtime'], '22:00')
        self.assertEqual(sleep['bedtime_day'], -1)
        self.assertEqual(sleep['wake_time'], '08:00')
        self.assertEqual(sleep['sleep_satisfaction'], 8)
        self.assertIsNone(sleep['mood_control'])
        self.assertEqual(sleep['completed'], 0)
        self.assertIsNone((await database.get_user_profile(100))['last_entry_at'])
        self.assertEqual((await self.state.get_data())['date'], self.yesterday.isoformat())
        for label in ('7', 'No', 'No'):
            await self.click(self.button_data(label))
        other = await get_day_entry(100, self.yesterday)
        self.assertEqual(other['mood_control'], 7)
        self.assertEqual(other['ache'], 0)
        self.assertIsNone(other['bedtime'])
        self.assertEqual(other['day_section_complete'], 1)
        self.assertEqual(other['completed'], 0)
        self.assertEqual(other['next_step'], 'bedtime')
        self.assertIsNone(await get_morning_session(100))
        self.assertIsNone(await self.state.get_state())
        self.assertIsNotNone((await database.get_user_profile(100))['last_entry_at'])
        self.assertFalse(await morning_entry_needed(100, self.today))

    async def test_completed_yesterday_is_preserved_and_only_sleep_is_asked(self):
        await self.finish_edit(self.yesterday.isoformat())
        before = await get_day_entry(100, self.yesterday)
        await self.open_morning()
        await self.save_sleep()
        self.assertEqual(await get_day_entry(100, self.yesterday), before)
        self.assertIsNone(await get_morning_session(100))
        self.assertIn('Entry saved!', self.screen_text())

    async def test_saved_sleep_is_skipped_and_yesterdays_draft_continues(self):
        for field, value, next_step in (
            ('bedtime', '21:00', 'wake_time'), ('wake_time', '07:00', 'sleep_satisfaction'),
            ('sleep_satisfaction', 9, 'mood_control'),
        ):
            await save_day_answer(100, self.today, field, value, next_step)
        await save_day_answer(100, self.yesterday, 'mood_control', 6, 'ache')
        sleep = await get_day_entry(100, self.today)
        await self.open_morning()
        self.assertEqual((await self.state.get_data())['step'], 'ache')
        for label in ('No', 'No'):
            await self.click(self.button_data(label))
        self.assertEqual(await get_day_entry(100, self.today), sleep)
        self.assertEqual((await get_day_entry(100, self.yesterday))['mood_control'], 6)
        self.assertIsNone(await get_morning_session(100))

    async def test_reopening_completed_sections_does_not_write_or_reset_timer(self):
        await self.finish_edit(self.yesterday.isoformat())
        await self.finish_edit(self.today.isoformat())
        before = {day: await get_day_entry(100, day) for day in (self.today, self.yesterday)}
        profile = await database.get_user_profile(100)
        await self.open_morning()
        self.assertIn('Both sections are complete', self.screen_text())
        self.assertIsNone(await get_morning_session(100))
        self.assertEqual(await database.get_user_profile(100), profile)
        for day, entry in before.items():
            self.assertEqual(await get_day_entry(100, day), entry)

    async def test_restart_and_old_reminder_resume_the_original_dates(self):
        await self.open_morning()
        await self.click(self.button_data('22:00'))
        session = await get_morning_session(100)
        await self.state.clear()
        await database.init_db()
        with patch('Handlers.morning.today_for_user', return_value=self.today + timedelta(days=1)):
            await self.click(f'morning:open:{self.today.isoformat()}')
            resume = f"morning:resume:{session['session_id']}"
            self.assertIn(resume, [b.callback_data for row in self.keyboard().inline_keyboard for b in row])
            await self.click(resume)
        draft = await self.state.get_data()
        self.assertEqual(draft['date'], self.today.isoformat())
        self.assertEqual(draft['step'], 'wake_time')
        self.assertEqual((await get_morning_session(100))['other_date'], self.yesterday.isoformat())
        self.assertEqual((await get_day_entry(100, self.today))['bedtime'], '22:00')

    async def test_duplicate_answer_does_not_advance_the_morning_twice(self):
        await self.open_morning()
        old_message = self.current_message_id
        answer = self.button_data('22:00')
        await self.click(answer)
        entry = await get_day_entry(100, self.today)
        await self.click(answer, message_id=old_message)
        self.assertTrue(self.acknowledge.call_args.kwargs['show_alert'])
        self.assertEqual(await get_day_entry(100, self.today), entry)
        self.assertEqual((await get_morning_session(100))['step'], 'wake_time')

    async def test_negative_sleep_cannot_overwrite_existing_wake_time(self):
        await save_day_answer(100, self.today, 'wake_time', '08:00', 'bedtime')
        before = await get_day_entry(100, self.today)
        await self.open_morning()
        await self.command('today 10:00')
        self.assertIn('Sleep duration cannot be negative.', self.screen_text())
        self.assertEqual(await get_day_entry(100, self.today), before)
        session = await get_morning_session(100)
        self.assertEqual(session['step'], 'bedtime')
        self.assertEqual(session['answers_count'], 0)

    async def test_explicit_sleep_edit_preserves_other_answers_and_shows_previous_values(self):
        await self.finish_edit(self.yesterday.isoformat())
        await self.finish_edit(self.today.isoformat())
        yesterday = await get_day_entry(100, self.yesterday)
        today = await get_day_entry(100, self.today)
        await self.open_morning('begin', 'sleep')
        self.assertIn('21:00', self.screen_text())
        question_id = self.current_message_id
        await self.click(self.button_data('22:00'))
        self.assertIn('21:00', self.screens[question_id]['text'])
        self.assertIn('22:00', self.screens[question_id]['text'])
        for label in ('08:00', '9'):
            await self.click(self.button_data(label))
        updated = await get_day_entry(100, self.today)
        self.assertEqual(updated['sleep_satisfaction'], 9)
        self.assertEqual(updated['mood_control'], today['mood_control'])
        self.assertEqual(updated['ache'], today['ache'])
        self.assertEqual(updated['completed'], 1)
        self.assertEqual(await get_day_entry(100, self.yesterday), yesterday)
        self.assertIsNone(await get_morning_session(100))

    async def test_medication_pain_details_and_note_are_saved_for_yesterday(self):
        await self.open_morning()
        for label in ('22:00', '08:00', '8', '7', 'Yes', '6', 'Yes'):
            await self.click(self.button_data(label))
        await self.command('Test medicine')
        for label in ('A little', 'No', 'Yes'):
            await self.click(self.button_data(label))
        for _ in range(4):
            await self.click(self.button_data('☐ Skip'))
            await self.click(self.button_data('Done'))
        await self.click(self.button_data('No'))
        await self.click(self.button_data('Yes'))
        await self.command('Yesterday note')
        medicines = await get_medications(100, self.yesterday)
        self.assertEqual([(m['description'], m['relief']) for m in medicines], [('Test medicine', 'a_little')])
        self.assertEqual(await get_medications(100, self.today), [])
        answers, _ = await get_pain_answers(100, self.yesterday, self.yesterday)
        self.assertEqual([a['status'] for a in answers], ['skipped'] * 4)
        self.assertEqual(await get_pain_answers(100, self.today, self.today), ([], []))
        self.assertEqual((await get_day_entry(100, self.yesterday))['day_comment'], 'Yesterday note')
        self.assertIsNone(await get_morning_session(100))

    async def test_migration_preserves_old_completed_entries_and_unknown_timestamps(self):
        await self.finish_edit(self.yesterday.isoformat())
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute('UPDATE diary_entries SET updated_at = NULL')
            await db.execute('ALTER TABLE diary_entries DROP COLUMN day_section_complete')
            await db.execute('DROP TABLE user_consents')
            await db.execute('DROP TABLE morning_sessions')
            await db.commit()
        before = await get_day_entry(100, self.yesterday)
        await database.init_db()
        migrated = await get_day_entry(100, self.yesterday)
        self.assertEqual({key: migrated[key] for key in before}, before)
        self.assertEqual(migrated['day_section_complete'], 1)
        self.assertIsNone(migrated['updated_at'])
        self.assertEqual(await database.get_legacy_answer(100, date(2024, 2, 10)), 1)
        await database.init_db()
        self.assertEqual(await get_day_entry(100, self.yesterday), migrated)
