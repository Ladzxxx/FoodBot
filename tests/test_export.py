from datetime import date
from io import BytesIO
import sqlite3
import unittest
from openpyxl import load_workbook
import aiosqlite
import database
from privacy_storage import accept_consent
from day_storage import get_export_data, save_day_answer, add_meal
from day_export import make_excel_file
from pain_storage import save_pain_choice
from helpers import BotTests


class ExportTests(BotTests):
    async def test_old_export_button_uses_current_language_and_preserves_values(self):
        await self.command('/statistics')
        statistics_id = self.current_message_id
        callback = self.button_data('Get Excel file')
        before = await get_export_data(100)
        for lang, filename, title, header in (
            ('ru', 'foodbot_дневник.xlsx', 'Ответы дневника', 'Дата'),
            ('en', 'foodbot_answers.xlsx', 'Diary answers', 'Date'),
        ):
            await self.command('/language')
            await self.click('language:' + lang)
            await self.click(callback, message_id=statistics_id)
            document = self.screens[self.current_message_id]['document']
            self.assertEqual(document.filename, filename)
            workbook = load_workbook(BytesIO(document.data))
            try:
                sheet = workbook.active
                self.assertEqual(sheet.title, title)
                self.assertEqual(sheet['A1'].value, header)
                self.assertEqual([row[0].date() for row in sheet.iter_rows(min_row=2,values_only=True)],
                                 [date(2024,2,11), date(2024,2,10)])
            finally:
                workbook.close()
        self.assertEqual(await get_export_data(100), before)

    async def test_file_has_all_answers_descending_dates_and_no_other_users(self):
        day = date(2024, 2, 12)
        await save_day_answer(100, day, 'bedtime', '22:00', 'wake_time')
        await save_day_answer(100, day, 'wake_time', '08:00', 'sleep_satisfaction')
        await save_day_answer(100, day, 'sleep_satisfaction', 9, 'mood_control')
        await save_day_answer(100, day, 'ache', 1, 'pain_intensity')
        await save_day_answer(100, day, 'pain_intensity', 8, 'pain_description_requested')
        await save_day_answer(100, day, 'day_comment', '=SUM(1,2)', 'pain_description_requested')
        await save_day_answer(100, day, 'pain_description_requested', 1, 'pain_location')
        await save_pain_choice(100, day, 'pain_location', 'upper_right')
        await save_pain_choice(100, day, 'pain_location', 'other', 'A scar & <test>')
        await save_pain_choice(100, day, 'pain_location', 'done')
        await save_pain_choice(100, day, 'pain_character', 'cramping')
        await add_meal(100, date(2026, 11, 2), '12:34', 1, 3, 'Rice')
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("INSERT INTO day_medications (user_id, entry_date, description, relief) VALUES (100, '2024-02-12', 'Medicine A 10 mg', 'a_little')")
            await db.execute("INSERT INTO day_ratings VALUES (100, '2024-02-12', 5, 6, 4)")
            await db.execute("INSERT INTO calendar_answers VALUES (200, '2026-11-03', 1)")
            await db.commit()
        observer = sqlite3.connect(database.DB_PATH)
        try:
            version = observer.execute('PRAGMA data_version').fetchone()[0]
            await self.click('statistics:excel')
            self.assertEqual(observer.execute('PRAGMA data_version').fetchone()[0], version)
        finally:
            observer.close()
        document = self.screens[self.current_message_id]['document']
        self.assertEqual(document.filename, 'foodbot_answers.xlsx')
        workbook = load_workbook(BytesIO(document.data))
        self.addCleanup(workbook.close)
        sheet = workbook.active
        headers = [cell.value for cell in sheet[1]]
        rows = [dict(zip(headers, row)) for row in sheet.iter_rows(min_row=2, values_only=True)]
        self.assertEqual([row['Date'].date() for row in rows], [date(2026, 11, 2), day, date(2024, 2, 11), date(2024, 2, 10)])
        entry = rows[1]
        self.assertEqual(entry['Entry status'], 'Draft')
        self.assertEqual(entry['Bedtime date'].date(), date(2024, 2, 11))
        self.assertEqual(entry['Sleep satisfaction (1–10)'], 9)
        self.assertEqual(entry['Stomach pain'], 'Yes')
        self.assertEqual(entry['Day comment'], '=SUM(1,2)')
        cell = sheet.cell(3, headers.index('Day comment') + 1)
        self.assertEqual(cell.data_type, 's')
        self.assertEqual(entry['Legacy food (1–7)'], 6)
        self.assertIn('Medicine A 10 mg', entry['Medications and effect'])
        self.assertIn('A little', entry['Medications and effect'])
        self.assertIn('Other area: A scar & <test>', entry['Pain location answers'])
        self.assertEqual(entry['Pain location status'], 'Answered')
        self.assertEqual(entry['Pain character status'], 'In progress')
        self.assertIn('Rice', rows[0]['Meals (local time and description)'])
        self.assertEqual(sheet.freeze_panes, 'C2')
        self.assertTrue(sheet.auto_filter.ref)
        self.assertTrue(sheet['A1'].font.bold)

    async def test_export_is_all_time_from_both_statistics_menus_and_keeps_draft(self):
        for callback in ('statistics:month:2024-02-01', 'statistics:all:0'):
            await self.click(callback)
            export = self.button_data('Get Excel file')
            source_id = self.current_message_id
            await self.open_day_edit()
            before = await self.state.get_data()
            await self.click(export, message_id=source_id)
            self.assertEqual(await self.state.get_data(), before)
            self.assertIsNotNone(self.screens[self.current_message_id]['document'])

    async def test_empty_user_gets_no_empty_workbook(self):
        await database.ensure_user_profile(200, 200)
        await accept_consent(200, 'ru')
        await self.click('statistics:excel', user_id=200)
        self.assertIn('Пока нет записей', self.screen_text())
        self.assertEqual(self.document.call_count, 0)


class WorkbookTests(unittest.TestCase):
    def test_long_text_is_preserved_in_continuation_columns_and_empty_data(self):
        self.assertIsNone(make_excel_file({}))
        long_text = 'x' * 40000
        content = make_excel_file({'diary_entries': [{'entry_date': '2026-11-02', 'day_comment': long_text}]})
        workbook = load_workbook(BytesIO(content))
        self.addCleanup(workbook.close)
        sheet = workbook.active
        columns = [cell.column for cell in sheet[1] if str(cell.value).startswith('Day comment') and cell.value != 'Day comment requested']
        self.assertEqual(''.join(sheet.cell(2, column).value or '' for column in columns), long_text)
        self.assertEqual(sheet.max_row, 2)
