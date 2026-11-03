from datetime import date
import aiosqlite
import database
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import DeleteMessage, EditMessageText
from day_storage import save_day_answer, reset_day_draft, get_day_entry
from pain_storage import get_pain_answers, save_pain_choice
from Handlers.statistics import pain_statistics_pages
from Forms.pain import PAIN_QUESTIONS, PAIN_OPTIONS
from helpers import BotTests

DAY = date(2024, 2, 12)


class PainTests(BotTests):
    async def test_failed_confirmation_keeps_previous_message_and_resumes_saved_next_step(self):
        await self.enter_block()
        await self.choose('Upper left')
        draft = await self.state.get_data()
        previous = draft['pain_confirmation_id']
        self.edit.side_effect = TelegramNetworkError(method=EditMessageText(chat_id=100, message_id=draft['message_id'], text='test'), message='synthetic failure')
        with self.assertRaises(TelegramNetworkError):
            await self.click(self.button_data('Done'))
        self.assertIn(previous, self.screens)
        self.assertEqual((await self.read_entry())['next_step'], 'pain_character')
        self.edit.side_effect = self.edit_message
        await self.state.clear()
        await self.open_day_edit()
        self.assertIn('What did the pain feel like?', self.screen_text())
        await self.choose('Sharp/stabbing')
        self.api_delete.side_effect = TelegramBadRequest(method=DeleteMessage(chat_id=100, message_id=previous), message="message can't be deleted")
        await self.state.update_data(pain_confirmation_id=previous)
        await self.click(self.button_data('Done'))
        self.assertIn('What other symptoms', self.screen_text())

    async def enter_block(self):
        await self.open_day_edit()
        for label in ('21:00', '08:00', '8', '7', 'Yes', '6', 'No', 'Yes'):
            await self.click(self.button_data(label))

    async def choose(self, label):
        await self.click(self.button_data('☐ ' + label))

    async def test_four_questions_other_warning_and_completion(self):
        await self.enter_block()
        self.assertIn('Describe the worst pain episode on 12.02.2024', self.screen_text())
        self.assertIn('sudden severe pain', self.screen_text())
        self.assertEqual([[b.text[2:] for b in row] for row in self.keyboard().inline_keyboard[:3]], [
            ['Upper right', 'Upper middle', 'Upper left'], ['Middle right', 'Around navel', 'Middle left'], ['Lower right', 'Lower middle', 'Lower left']])
        await self.choose('Upper right')
        await self.choose('Lower left')
        await self.choose('Other area')
        await self.command('Near scar <test>')
        self.assertIn('Other area: Near scar <test>', self.screen_text())
        self.api_delete.assert_not_awaited()
        confirmation = self.current_message_id
        await self.click(self.button_data('Done'))
        self.assertIn('Answer recorded', self.screens[confirmation]['text'])
        await self.choose('Cramping')
        await self.choose('Burning')
        await self.click(self.button_data('Done'))
        self.assertNotIn(confirmation, self.screens)
        await self.choose('Fainting')
        await self.choose('Nausea')
        self.assertEqual(self.screen_text().count('seek urgent medical help'), 1)
        await self.click(self.button_data('Done'))
        self.assertEqual(len(PAIN_OPTIONS['pain_triggers']), 9)
        await self.choose('Stress or anxiety')
        await self.choose('Other')
        await self.command('A possible food, not a confirmed cause')
        await self.click(self.button_data('Done'))
        self.assertIn('note about the pain episode', self.screen_text())
        await self.click(self.button_data('No'))
        self.assertIn('note about the day?', self.screen_text())
        await self.click(self.button_data('No'))
        self.assertEqual((await self.read_entry())['completed'], 1)
        answers, options = await get_pain_answers(100, DAY, DAY)
        self.assertEqual([a['status'] for a in answers], ['answered'] * 4)
        self.assertEqual(len([o for o in options if o['is_selected']]), 9)

    async def test_empty_done_controls_pause_restart_and_stale_buttons(self):
        await self.enter_block()
        stale = self.button_data('☐ Upper right')
        old_message = self.current_message_id
        await self.click(self.button_data('Done'))
        self.assertIn('Choose an answer', self.acknowledge.call_args.args[0])
        await self.choose('Upper right')
        await self.choose('All over the abdomen')
        self.assertIsNotNone(self.button_data('☐ Upper right'))
        await self.choose('Not sure')
        self.assertIsNotNone(self.button_data('☐ All over the abdomen'))
        await self.choose('Skip')
        self.assertIsNotNone(self.button_data('☐ Not sure'))
        await self.choose('Lower middle')
        await self.click(self.button_data('Pause and return'))
        await database.init_db()
        await self.state.clear()
        await self.open_day_edit()
        self.assertIsNotNone(self.button_data('☑ Lower middle'))
        before = await get_pain_answers(100, DAY, DAY)
        await self.click(stale, message_id=old_message)
        await self.click(self.button_data('☐ Upper right'), user_id=200)
        self.assertEqual(await get_pain_answers(100, DAY, DAY), before)
        self.assertEqual(await get_pain_answers(200, DAY, DAY), ([], []))

    async def test_limits_none_skip_and_read_only_views(self):
        await self.enter_block()
        await self.choose('Other area')
        await self.command('x' * 201)
        self.assertEqual(await get_pain_answers(100, DAY, DAY), ([], []))
        await self.command('x' * 200)
        await self.click(self.button_data('Done'))
        await self.choose('Skip')
        await self.click(self.button_data('Done'))
        await self.choose('Nausea')
        await self.choose('None')
        self.assertIsNotNone(self.button_data('☐ Nausea'))
        await self.click(self.button_data('Done'))
        await self.choose('Other')
        await self.command('x' * 301)
        self.assertIn('1 and 300', self.screen_text())
        await self.command('x' * 300)
        await self.choose('No clear trigger')
        await self.click(self.button_data('Done'))
        before = await get_pain_answers(100, DAY, DAY)
        await self.click('painview:2024-02-12:0')
        while any(b.text == 'Next →' for row in self.keyboard().inline_keyboard for b in row):
            await self.click(self.button_data('Next →'))
        await self.click('painstats:2024-02-01:0')
        self.assertEqual(await get_pain_answers(100, DAY, DAY), before)

    async def test_statistics_denominators_unique_dates_and_users(self):
        statuses = ('answered', 'none', 'unknown', 'skipped', 'in_progress')
        entries = {}
        for day_number, status in enumerate(statuses, 1):
            day = date(2024, 2, day_number)
            await save_day_answer(100, day, 'ache', 1, 'pain_symptoms')
            await save_day_answer(100, day, 'pain_description_requested', 1, 'pain_symptoms')
            for _ in range(3):
                await save_pain_choice(100, day, 'pain_symptoms', 'nausea')
            if status == 'answered':
                await save_pain_choice(100, day, 'pain_symptoms', 'bloating')
                await save_day_answer(100, day, 'pain_intensity', 8, 'pain_symptoms')
            elif status != 'in_progress':
                await save_pain_choice(100, day, 'pain_symptoms', status)
            if status != 'in_progress':
                await save_pain_choice(100, day, 'pain_symptoms', 'done')
            entries[day.isoformat()] = await get_day_entry(100, day)
        answers, options = await get_pain_answers(100, date(2024, 2, 1), date(2024, 2, 28))
        pages = pain_statistics_pages(entries, answers, options)
        text = pages[2]
        self.assertIn('N = 2 confirmed dates', text)
        self.assertIn('Nausea: 1 (50.0%)', text)
        self.assertIn('Bloating: 1 (50.0%)', text)
        for label in ('Not sure: 1', 'Skipped: 1', 'In progress: 1', 'Average pain intensity: 8.00/10 (N = 1)'):
            self.assertIn(label, text)
        self.assertIn('No data yet', pain_statistics_pages({}, [], [])[0])
        self.assertEqual(await get_pain_answers(200), ([], []))
        async with aiosqlite.connect(database.DB_PATH) as db:
            rows = await db.execute_fetchall('SELECT option_code, COUNT(*) FROM day_pain_options GROUP BY user_id, entry_date, question_key, option_code HAVING COUNT(*) > 1')
        self.assertEqual(rows, [])

    async def test_clean_draft_deletes_pain_only_for_that_user_and_day(self):
        await self.enter_block()
        await self.choose('Upper left')
        await reset_day_draft(200, DAY)
        self.assertTrue((await get_pain_answers(100, DAY, DAY))[0])
        await reset_day_draft(100, DAY)
        self.assertEqual(await get_pain_answers(100, DAY, DAY), ([], []))
        async with aiosqlite.connect(database.DB_PATH) as db:
            rows = await db.execute_fetchall('SELECT answer FROM calendar_answers WHERE user_id = 100 ORDER BY entry_date')
        self.assertEqual(rows, [(1,), (0,)])
