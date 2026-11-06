import calendar
from datetime import date
from time import time

import aiosqlite

import database


async def get_export_data(user_id: int) -> dict:
    # Один снимок чтения: ответы не разойдутся между таблицами во время выгрузки.
    tables = ("diary_entries", "day_medications", "meals", "day_pain_answers",
              "day_pain_options", "calendar_answers", "day_ratings")
    data = {}
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("BEGIN")
        for table in tables:
            # Имена таблиц заданы выше, пользователь передаётся параметром.
            async with db.execute(f"SELECT * FROM {table} WHERE user_id = ? ORDER BY entry_date DESC", (user_id,)) as cursor:
                data[table] = [dict(row) for row in await cursor.fetchall()]
    return data


async def get_month_entries(user_id: int, year: int, month: int) -> dict:
    first = date(year, month, 1).isoformat()
    last = date(year, month, calendar.monthrange(year, month)[1]).isoformat()
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM diary_entries WHERE user_id = ? AND entry_date BETWEEN ? AND ?
        """, (user_id, first, last)) as cursor:
            rows = await cursor.fetchall()
    return {row["entry_date"]: dict(row) for row in rows}


async def get_day_entry(user_id: int, selected_date: date) -> dict | None:
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM diary_entries WHERE user_id = ? AND entry_date = ?
        """, (user_id, selected_date.isoformat())) as cursor:
            row = await cursor.fetchone()
    return dict(row) if row is not None else None


async def save_day_answer(user_id: int, selected_date: date, field: str, value, next_step: str, *, bedtime_day: int = -1, morning_id=None, flow_next_step=None):
    fields = (
        "bedtime", "wake_time", "sleep_satisfaction", "mood_control", "ache",
        "pain_intensity", "painkillers", "more_medicine", "day_comment_wanted",
        "day_comment", "pain_description_requested", "pain_comment_wanted", "pain_comment",
    )
    # Имя столбца проверено по списку, а ответ передаётся параметром.
    if field not in fields:
        raise ValueError("Unknown day field")
    if field == "bedtime" and bedtime_day not in (-1, 0):
        raise ValueError("Invalid bedtime day")
    day = selected_date.isoformat()
    completed = int(next_step == "complete")
    async with aiosqlite.connect(database.DB_PATH) as db:
        await db.execute("""
            INSERT INTO diary_entries (user_id, entry_date) VALUES (?, ?)
            ON CONFLICT(user_id, entry_date) DO NOTHING
        """, (user_id, day))
        # Утренний сон не меняет уже сохранённый прогресс других вопросов сегодня.
        old = await db.execute_fetchall(
            "SELECT next_step, day_section_complete, completed FROM diary_entries WHERE user_id = ? AND entry_date = ?", (user_id, day))
        old_step = old[0][0]
        await db.execute(f"""
            UPDATE diary_entries SET {field} = ?, next_step = ?, completed = ?, updated_at = ?
            WHERE user_id = ? AND entry_date = ?
        """, (value, next_step, completed, int(time()), user_id, day))
        if field == "bedtime":
            await db.execute("UPDATE diary_entries SET bedtime_day = ? WHERE user_id = ? AND entry_date = ?", (bedtime_day, user_id, day))
        if field == "ache" and not value:
            await db.execute("""
                UPDATE diary_entries SET pain_intensity = NULL, painkillers = NULL,
                    more_medicine = NULL, pain_description_requested = NULL,
                    pain_comment_wanted = NULL, pain_comment = NULL
                WHERE user_id = ? AND entry_date = ?
            """, (user_id, day))
        if (field == "ache" or field == "painkillers") and not value:
            await db.execute("DELETE FROM day_medications WHERE user_id = ? AND entry_date = ?", (user_id, day))
        if field == "painkillers":
            await db.execute("UPDATE diary_entries SET more_medicine = NULL WHERE user_id = ? AND entry_date = ?", (user_id, day))
        if field == "day_comment_wanted" and not value:
            await db.execute("UPDATE diary_entries SET day_comment = '' WHERE user_id = ? AND entry_date = ?", (user_id, day))
        if field == "pain_comment_wanted" and not value:
            await db.execute("UPDATE diary_entries SET pain_comment = '' WHERE user_id = ? AND entry_date = ?", (user_id, day))
        if field in ("bedtime", "wake_time", "sleep_satisfaction") and (morning_id or (old[0][1] and not old[0][2])):
            rows = await db.execute_fetchall(
                "SELECT bedtime, wake_time, sleep_satisfaction FROM diary_entries WHERE user_id = ? AND entry_date = ?",
                (user_id, day))
            missing = next((key for key, value in zip(("bedtime", "wake_time", "sleep_satisfaction"), rows[0])
                if value is None), None)
            normal_step = missing or (old_step if old_step not in ("bedtime", "wake_time", "sleep_satisfaction", "complete") else "mood_control")
            await db.execute("UPDATE diary_entries SET next_step = ? WHERE user_id = ? AND entry_date = ?",
                (normal_step, user_id, day))
        else:
            await db.execute("UPDATE diary_entries SET day_section_complete = ? WHERE user_id = ? AND entry_date = ?",
                (completed, user_id, day))
        await db.execute("""UPDATE diary_entries SET completed =
            (day_section_complete = 1 AND bedtime IS NOT NULL AND wake_time IS NOT NULL AND sleep_satisfaction IS NOT NULL)
            WHERE user_id = ? AND entry_date = ?""", (user_id, day))
        await db.execute("UPDATE diary_entries SET next_step = 'complete' WHERE user_id = ? AND entry_date = ? AND completed = 1",
            (user_id, day))
        # У завершённой части дня может ещё не быть сна за эту же дату.
        rows = await db.execute_fetchall(
            "SELECT bedtime, wake_time, sleep_satisfaction, completed FROM diary_entries WHERE user_id = ? AND entry_date = ?",
            (user_id, day))
        missing = next((key for key, value in zip(("bedtime", "wake_time", "sleep_satisfaction"), rows[0][:3])
            if value is None), None)
        if completed and missing:
            await db.execute("UPDATE diary_entries SET next_step = ? WHERE user_id = ? AND entry_date = ?",
                (missing, user_id, day))
        if morning_id:
            await db.execute("UPDATE morning_sessions SET step = ?, answers_count = answers_count + 1 WHERE user_id = ? AND session_id = ?",
                (flow_next_step, user_id, morning_id))
        elif completed and rows[0][3]:
            await db.execute("UPDATE user_profiles SET last_entry_at = ? WHERE user_id = ?", (int(time()), user_id))
        await db.commit()


async def get_medications(user_id: int, selected_date: date) -> list[dict]:
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, description, relief FROM day_medications
            WHERE user_id = ? AND entry_date = ? ORDER BY id
        """, (user_id, selected_date.isoformat())) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def add_medication(user_id: int, selected_date: date, description: str, replace_existing: bool, *, morning_id=None, flow_next_step=None):
    day = selected_date.isoformat()
    async with aiosqlite.connect(database.DB_PATH) as db:
        if replace_existing:
            await db.execute("DELETE FROM day_medications WHERE user_id = ? AND entry_date = ?", (user_id, day))
        await db.execute("""
            INSERT INTO day_medications (user_id, entry_date, description) VALUES (?, ?, ?)
        """, (user_id, day, description))
        await db.execute("""
            UPDATE diary_entries SET next_step = 'medicine_relief', completed = 0, updated_at = ?
            WHERE user_id = ? AND entry_date = ?
        """, (int(time()), user_id, day))
        if morning_id:
            await db.execute("UPDATE morning_sessions SET step = ?, answers_count = answers_count + 1 WHERE user_id = ? AND session_id = ?",
                (flow_next_step, user_id, morning_id))
        await db.commit()


async def save_medication_relief(user_id: int, selected_date: date, relief: str, *, morning_id=None, flow_next_step=None):
    day = selected_date.isoformat()
    async with aiosqlite.connect(database.DB_PATH) as db:
        await db.execute("""
            UPDATE day_medications SET relief = ? WHERE id = (
                SELECT id FROM day_medications WHERE user_id = ? AND entry_date = ?
                ORDER BY id DESC LIMIT 1
            )
        """, (relief, user_id, day))
        await db.execute("""
            UPDATE diary_entries SET next_step = 'more_medicine', completed = 0, updated_at = ?
            WHERE user_id = ? AND entry_date = ?
        """, (int(time()), user_id, day))
        if morning_id:
            await db.execute("UPDATE morning_sessions SET step = ?, answers_count = answers_count + 1 WHERE user_id = ? AND session_id = ?",
                (flow_next_step, user_id, morning_id))
        await db.commit()


async def reset_day_draft(user_id: int, selected_date: date) -> bool:
    day = selected_date.isoformat()
    async with aiosqlite.connect(database.DB_PATH) as db:
        for table in ('day_pain_answers', 'day_pain_options'):
            await db.execute(f'''DELETE FROM {table} WHERE user_id = ? AND entry_date = ?
                AND EXISTS (SELECT 1 FROM diary_entries WHERE user_id = ? AND entry_date = ? AND completed = 0)''', (user_id, day, user_id, day))
        await db.execute("""
            DELETE FROM day_medications WHERE user_id = ? AND entry_date = ?
                AND EXISTS (SELECT 1 FROM diary_entries
                    WHERE user_id = ? AND entry_date = ? AND completed = 0)
        """, (user_id, day, user_id, day))
        cursor = await db.execute("DELETE FROM diary_entries WHERE user_id = ? AND entry_date = ? AND completed = 0", (user_id, day))
        await db.commit()
        return cursor.rowcount == 1


async def add_meal(user_id: int, selected_date: date, meal_time: str, created_at: int, utc_offset: int, comment: str = "") -> int:
    async with aiosqlite.connect(database.DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO meals (user_id, entry_date, meal_time, created_at, utc_offset, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, selected_date.isoformat(), meal_time, created_at, utc_offset, comment))
        await db.commit()
        return cursor.lastrowid


async def update_meal_comment(user_id: int, meal_id: int, comment: str):
    async with aiosqlite.connect(database.DB_PATH) as db:
        await db.execute("UPDATE meals SET comment = ? WHERE id = ? AND user_id = ?", (comment, meal_id, user_id))
        await db.commit()


async def get_meal(user_id: int, meal_id: int):
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT * FROM meals WHERE user_id = ? AND id = ?", (user_id, meal_id))
    return dict(rows[0]) if rows else None


async def update_meal_time(user_id: int, meal_id: int, meal_time: str) -> bool:
    from Forms.meal import parse_meal_time
    meal_time = parse_meal_time(meal_time)
    async with aiosqlite.connect(database.DB_PATH) as db:
        # Меняем только часы; дата, комментарий и время создания остаются прежними.
        cursor = await db.execute("UPDATE meals SET meal_time = ? WHERE user_id = ? AND id = ?",
            (meal_time, user_id, meal_id))
        await db.commit()
        return cursor.rowcount == 1


async def get_meals(user_id: int, first_day: date | None = None, last_day: date | None = None) -> list[dict]:
    first = (first_day or date.min).isoformat()
    last = (last_day or first_day or date.max).isoformat()
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM meals WHERE user_id = ? AND entry_date BETWEEN ? AND ?
            ORDER BY entry_date, meal_time, created_at, id
        """, (user_id, first, last)) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_meal_counts(user_id: int, first_day: date, last_day: date) -> dict:
    async with aiosqlite.connect(database.DB_PATH) as db:
        async with db.execute("""
            SELECT entry_date, COUNT(*) FROM meals
            WHERE user_id = ? AND entry_date BETWEEN ? AND ? GROUP BY entry_date
        """, (user_id, first_day.isoformat(), last_day.isoformat())) as cursor:
            rows = await cursor.fetchall()
    return dict(rows)


async def get_all_entries(user_id: int) -> dict:
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM diary_entries WHERE user_id = ? ORDER BY entry_date", (user_id,)) as cursor:
            rows = await cursor.fetchall()
    return {row["entry_date"]: dict(row) for row in rows}


async def get_recent_entries(user_id: int, today: date, limit: int = 8) -> list[dict]:
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM diary_entries WHERE user_id = ? AND entry_date <= ?
            ORDER BY entry_date DESC LIMIT ?
        """, (user_id, today.isoformat(), limit)) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_legacy_entries(user_id: int) -> list[dict]:
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT entry_date, 'yes_no' AS kind FROM calendar_answers WHERE user_id = ?
            UNION ALL SELECT entry_date, 'ratings' AS kind FROM day_ratings WHERE user_id = ?
        """, (user_id, user_id)) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]
