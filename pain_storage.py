from datetime import date
from time import time
import aiosqlite
import database
from Forms.pain import PAIN_QUESTIONS, option_labels, next_pain_question


async def get_pain_answers(user_id, first=date.min, last=date.max):
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        answers = await db.execute_fetchall('SELECT * FROM day_pain_answers WHERE user_id = ? AND entry_date BETWEEN ? AND ? ORDER BY entry_date, question_key', (user_id, first.isoformat(), last.isoformat()))
        options = await db.execute_fetchall('SELECT * FROM day_pain_options WHERE user_id = ? AND entry_date BETWEEN ? AND ? ORDER BY entry_date, question_key, option_code', (user_id, first.isoformat(), last.isoformat()))
    return [dict(row) for row in answers], [dict(row) for row in options]


async def save_pain_choice(user_id, selected_date, key, code, custom_text=None):
    if key not in PAIN_QUESTIONS or (code != 'done' and code not in option_labels(key)):
        raise ValueError('pain.error.invalid_selection')
    if custom_text is not None and (code != 'other' or not 1 <= len(custom_text.strip()) <= (300 if key == 'pain_triggers' else 200)):
        raise ValueError('pain.error.invalid_text')
    day = selected_date.isoformat()
    params = (user_id, day, key)
    # Один UTC timestamp для всей транзакции, без SQL-функции времени.
    saved_at = int(time())
    async with aiosqlite.connect(database.DB_PATH) as db:
        # Проверка шага и изменение выбора выполняются под одной блокировкой SQLite.
        await db.execute('BEGIN IMMEDIATE')
        rows = await db.execute_fetchall('SELECT next_step, completed FROM diary_entries WHERE user_id = ? AND entry_date = ?', (user_id, day))
        if not rows or rows[0] != (key, 0):
            raise ValueError('pain.error.question_changed')
        rows = await db.execute_fetchall('SELECT option_code FROM day_pain_options WHERE user_id = ? AND entry_date = ? AND question_key = ? AND is_selected = 1', params)
        selected = {row[0] for row in rows}
        status = 'in_progress'
        next_step = key
        if code == 'done':
            if not selected:
                raise ValueError('pain.error.choose_first')
            status = next((item for item in ('none', 'unknown', 'skipped') if item in selected), 'answered')
            next_step = next_pain_question(key)
        else:
            enabled = int(code not in selected or custom_text is not None)
            if code == 'other' and enabled and custom_text is None:
                raise ValueError('pain.error.other_text')
            if enabled:
                if code in ('none', 'unknown', 'skipped'):
                    await db.execute('UPDATE day_pain_options SET is_selected = 0, updated_at = ? WHERE user_id = ? AND entry_date = ? AND question_key = ?', (saved_at, *params))
                else:
                    await db.execute("UPDATE day_pain_options SET is_selected = 0, updated_at = ? WHERE user_id = ? AND entry_date = ? AND question_key = ? AND option_code IN ('none','unknown','skipped')", (saved_at, *params))
                if key == 'pain_location' and code == 'all_over':
                    await db.execute("UPDATE day_pain_options SET is_selected = 0, updated_at = ? WHERE user_id = ? AND entry_date = ? AND question_key = ? AND option_code NOT IN ('all_over','other')", (saved_at, *params))
                elif key == 'pain_location' and code != 'other':
                    await db.execute("UPDATE day_pain_options SET is_selected = 0, updated_at = ? WHERE user_id = ? AND entry_date = ? AND question_key = ? AND option_code = 'all_over'", (saved_at, *params))
            await db.execute('''INSERT INTO day_pain_options VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, entry_date, question_key, option_code) DO UPDATE SET
                custom_text = excluded.custom_text, is_selected = excluded.is_selected, updated_at = excluded.updated_at''', (*params, code, custom_text.strip() if custom_text is not None else None, enabled, saved_at))
        await db.execute('''INSERT INTO day_pain_answers VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, entry_date, question_key) DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at''', (*params, status, saved_at))
        await db.execute('UPDATE diary_entries SET next_step = ?, updated_at = ? WHERE user_id = ? AND entry_date = ?', (next_step, saved_at, user_id, day))
        await db.commit()
    return next_step
