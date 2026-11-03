import asyncio
import ast
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path
from string import Formatter
from unittest.mock import AsyncMock, patch
import unittest
import aiosqlite
from openpyxl import load_workbook

import database
from localization import t, first_language, language_of
from Locales.en import TEXTS as EN
from Locales.ru import TEXTS as RU
from Keyboards.calendar import calendar_keyboard
from Keyboards.profile import profile_keyboard
from Keyboards.day import question_keyboard
from Keyboards.pain import pain_keyboard
from Forms.day import QUESTIONS
from Forms.profile import PROFILE_QUESTIONS
from Forms.pain import PAIN_OPTIONS
from reminders import send_due_reminders
from helpers import BotTests


class DictionaryTests(unittest.TestCase):
    def test_keys_placeholders_fallback_and_all_static_keys(self):
        self.assertEqual(set(EN), set(RU))
        def fields(text):
            return {name for literal, name, spec, conversion in Formatter().parse(text) if name is not None}
        for key in EN:
            with self.subTest(key=key):
                self.assertEqual(fields(EN[key]), fields(RU[key]))
                self.assertTrue(EN[key])
                self.assertTrue(RU[key])
        with self.assertRaises(KeyError):
            t('ru', 'missing.test.key')
        with patch.dict(RU, {}, clear=True):
            self.assertEqual(t('ru', 'common.yes'), 'Yes')
        self.assertEqual(language_of(None), 'ru')
        self.assertEqual(t(None, 'common.yes'), 'Да')
        files = [*Path('Handlers').glob('*.py'), *Path('Keyboards').glob('*.py'),
                 *Path('Forms').glob('*.py'), Path('day_export.py'), Path('reminders.py')]
        for file in files:
            tree = ast.parse(file.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 't' and len(node.args) >= 2:
                    if isinstance(node.args[1], ast.Constant):
                        self.assertIn(node.args[1].value, EN, f'{file}:{node.lineno}')

    def test_button_codes_and_scales_do_not_depend_on_language(self):
        def codes(keyboard):
            return [[b.callback_data for b in row] for row in keyboard.inline_keyboard]
        today = date(2026, 11, 3)
        self.assertEqual(codes(calendar_keyboard(today, {}, today, lang='ru')), codes(calendar_keyboard(today, {}, today, lang='en')))
        for field in PROFILE_QUESTIONS:
            a = profile_keyboard(field, {'reminder_period':'morning'}, lang='ru')
            b = profile_keyboard(field, {'reminder_period':'morning'}, lang='en')
            if a:
                self.assertEqual(codes(a), codes(b))
        for step in QUESTIONS:
            self.assertEqual(codes(question_keyboard('test', step, today, lang='ru')), codes(question_keyboard('test', step, today, lang='en')))
        for key in PAIN_OPTIONS:
            self.assertEqual(codes(pain_keyboard('test',key,[],lang='ru')),codes(pain_keyboard('test',key,[],lang='en')))


class LocalizationTests(BotTests):
    async def test_profile_language_is_read_once_for_calendar_and_statistics(self):
        with patch('Handlers.routes.get_user_profile', wraps=database.get_user_profile) as read:
            await self.command('/callendar')
            self.assertEqual(read.await_count,1)
        with patch('Handlers.statistics.get_user_profile', wraps=database.get_user_profile) as read:
            await self.command('/statistics')
            self.assertEqual(read.await_count,1)

    async def test_russian_pain_flow_notes_and_html_are_preserved(self):
        await self.seed_ru(100)
        await self.open_day_edit()
        for label in ('21:00','08:00','8','7','Да','6','Нет','Да'):
            await self.click(self.button_data(label))
        self.assertIn('Опишите самый сильный эпизод',self.screen_text())
        await self.click(self.button_data('☐ Другая область'))
        await self.command('Шрам <b>& тест')
        await self.click(self.button_data('Готово'))
        await self.click(self.button_data('☐ Схваткообразная'))
        await self.click(self.button_data('Готово'))
        await self.click(self.button_data('☐ Обморок'))
        self.assertIn('срочно обратитесь за медицинской помощью',self.screen_text())
        await self.click(self.button_data('Готово'))
        await self.click(self.button_data('☐ Нет явного триггера'))
        await self.click(self.button_data('Готово'))
        await self.click(self.button_data('Нет'))
        await self.click(self.button_data('Да'))
        note = 'Заметка <b>x</b> & y'
        await self.command(note)
        self.assertIn('Запись сохранена',self.screen_text())
        await self.click('calendar:day:2024-02-12')
        self.assertIn(note,self.screen_text())
        raw = self.screens[self.current_message_id]['text']
        self.assertIn('&lt;b&gt;',raw)
        self.assertNotIn('&amp;lt;b&gt;',raw)
        await self.click('painstats:2024-02-01:0')
        self.assertIn('Статистика боли: Февраль 2024',self.screen_text())
        self.assertIn('Другая область',self.screen_text())

    async def seed_ru(self, user_id=200):
        await database.ensure_user_profile(user_id, user_id)
        await database.save_profile_answer(user_id, 'utc_offset', 3)
        await database.save_profile_settings(user_id, dict(language='ru',nickname='Влад',gender='secret',birth_year=2000,utc_offset=3,reminder_period='morning',reminder_hour=9))
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute('UPDATE user_profiles SET setup_complete = 1 WHERE user_id = ?', (user_id,))
            await db.commit()

    async def test_name_guess_first_message_and_explicit_selection_wins(self):
        await self.command('/start', user_id=200, first_name='Влад')
        welcome = self.screens[self.message_events[-2][1]]
        self.assertIn('Привет!', welcome['text'])
        self.assertEqual(Path(welcome['photo'].path).name, 'RU-helloimage.png')
        self.assertTrue(Path(welcome['photo'].path).is_file())
        self.assertIsNone((await database.get_user_profile(200))['language'])
        await self.click('profile:language:en', user_id=200)
        self.assertIn('nickname', self.screen_text())
        self.assertEqual((await database.get_user_profile(200))['language'], 'en')
        await database.init_db()
        await self.command('/start', user_id=200, first_name='Влад')
        self.assertIn('nickname', self.screen_text())
        await self.command('/start', user_id=300, first_name='Vlad')
        self.assertIn("Hi, I'm Foodie!", self.screens[self.message_events[-2][1]]['text'])
        self.assertEqual(Path(self.screens[self.message_events[-2][1]]['photo'].path).name, 'helloimage.png')
        await self.click('profile:language:ru', user_id=300)
        self.assertIn('Введите никнейм', self.screen_text())
        self.assertEqual((await database.get_user_profile(300))['language'], 'ru')

    async def test_language_changes_only_language_and_keeps_pending_day(self):
        await self.open_day_edit()
        await self.click(self.button_data('21:00'))
        question_id = self.current_message_id
        wake = self.button_data('08:00')
        before_state = await self.state.get_data()
        before_entry = await self.read_entry()
        await database.disable_reminders(100)
        profile = await database.get_user_profile(100)
        await self.command('/language')
        await self.click('language:ru')
        self.assertIn('Язык сохранён', self.screen_text())
        self.assertEqual(await self.state.get_data(), before_state)
        self.assertEqual(await self.read_entry(), before_entry)
        self.assertEqual(await database.get_user_profile(100), {**profile, 'language':'ru'})
        await self.click(wake, message_id=question_id)
        self.assertIn('Насколько вы удовлетворены своим сном?', self.screen_text())

    async def test_two_users_and_russian_calendar_meal_statistics_export(self):
        await self.seed_ru()
        await asyncio.gather(self.command('/callendar',user_id=100), self.command('/callendar',user_id=200))
        texts = [s['text'] for s in self.screens.values()]
        self.assertTrue(any('Select a day' in text for text in texts))
        self.assertTrue(any('Выберите дату' in text for text in texts))
        await self.command('/meal <b>Soup & суп</b>', user_id=200)
        self.assertIn('Приём пищи сохранён', self.screen_text())
        self.assertIn('<b>Soup & суп</b>', self.screen_text())
        from day_storage import get_meals
        meals = await get_meals(200)
        await self.click('calendar:day:' + meals[0]['entry_date'], user_id=200)
        self.assertIn('Выбранный день',self.screen_text())
        await self.command('/statistics',user_id=200)
        self.assertIn('Статистика за всё время',self.screen_text())
        await self.click(self.button_data('Скачать Excel'),user_id=200)
        document = self.screens[self.current_message_id]['document']
        book = load_workbook(BytesIO(document.data))
        self.addCleanup(book.close)
        self.assertEqual(book.active.title,'Ответы дневника')
        self.assertEqual(book.active['A1'].value,'Дата')
        self.assertIn('<b>Soup & суп</b>',str(list(book.active.values)))

    async def test_settings_draft_language_and_reminders_use_saved_language(self):
        original = await database.get_user_profile(100)
        await self.command('/settings')
        await self.click('profile:language:ru')
        self.assertIn('Введите никнейм',self.screen_text())
        self.assertEqual(await database.get_user_profile(100),original)
        deliver = AsyncMock()
        with patch.object(self.bot,'send_message',deliver):
            await send_due_reminders(self.bot,datetime(2030,1,1,12,tzinfo=timezone.utc))
        self.assertEqual(deliver.call_args.kwargs['text'],"— Hi, it's Me!")
        for text in ('Влад',):
            await self.command(text)
        await self.click('profile:utc_offset:3')
        await self.click('profile:reminder_period:morning')
        await self.click('profile:reminder_hour:9')
        self.assertIn('Напоминания',self.screen_text())
        image_path = Path(self.screens[self.current_message_id]['photo'].path)
        self.assertEqual(image_path.name, 'RU-seeyousoon.png')
        self.assertTrue(image_path.is_file())
        self.assertEqual((await database.get_user_profile(100))['language'],'ru')
        with patch.object(self.bot,'send_message',deliver):
            await send_due_reminders(self.bot,datetime(2030,1,2,12,tzinfo=timezone.utc))
        self.assertEqual(deliver.call_args.kwargs['text'],'— Привет, это я!')

    async def test_missing_language_falls_back_to_russian_without_forcing_setup(self):
        await self.command('/help', user_id=300)
        self.assertIn('дневник сна',self.screen_text())
        self.assertIsNone(await database.get_user_profile(300))
