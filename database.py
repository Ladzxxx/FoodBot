import calendar
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from time import time

import aiosqlite

DB_PATH = Path(__file__).resolve().parent / "data" / "calendar.sqlite3"


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS calendar_answers (
                user_id INTEGER NOT NULL,
                entry_date TEXT NOT NULL,
                answer INTEGER NOT NULL CHECK (answer IN (0, 1)),
                PRIMARY KEY (user_id, entry_date)
            )
        """)
        # Прежнюю таблицу «Да/Нет» не меняем и не переводим её ответы в оценки.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS day_ratings (
                user_id INTEGER NOT NULL,
                entry_date TEXT NOT NULL,
                sleep INTEGER CHECK (sleep BETWEEN 1 AND 7),
                food INTEGER CHECK (food BETWEEN 1 AND 7),
                mood INTEGER CHECK (mood BETWEEN 1 AND 7),
                PRIMARY KEY (user_id, entry_date)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                language TEXT,
                nickname TEXT,
                gender TEXT,
                birth_year INTEGER,
                utc_offset INTEGER CHECK (utc_offset BETWEEN -11 AND 12),
                reminder_period TEXT,
                reminder_hour INTEGER CHECK (reminder_hour BETWEEN 0 AND 23),
                setup_complete INTEGER NOT NULL DEFAULT 0,
                reminder_started_at INTEGER,
                last_entry_at INTEGER,
                last_reminder_date TEXT,
                reminders_enabled INTEGER NOT NULL DEFAULT 1
            )
        """)
        # Схема нового дневника одобрена пользователем; прежние таблицы сохраняем.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS diary_entries (
                user_id INTEGER NOT NULL,
                entry_date TEXT NOT NULL,
                bedtime TEXT,
                bedtime_day INTEGER NOT NULL DEFAULT -1 CHECK (bedtime_day IN (-1, 0)),
                wake_time TEXT,
                sleep_satisfaction INTEGER CHECK (sleep_satisfaction BETWEEN 1 AND 10),
                mood_control INTEGER CHECK (mood_control BETWEEN 1 AND 10),
                ache INTEGER CHECK (ache IN (0, 1)),
                pain_intensity INTEGER CHECK (pain_intensity BETWEEN 1 AND 10),
                painkillers INTEGER CHECK (painkillers IN (0, 1)),
                more_medicine INTEGER CHECK (more_medicine IN (0, 1)),
                day_comment_wanted INTEGER CHECK (day_comment_wanted IN (0, 1)),
                day_comment TEXT,
                pain_description_requested INTEGER CHECK (pain_description_requested IN (0, 1)),
                pain_comment_wanted INTEGER CHECK (pain_comment_wanted IN (0, 1)),
                pain_comment TEXT,
                next_step TEXT NOT NULL DEFAULT 'bedtime',
                completed INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER,
                PRIMARY KEY (user_id, entry_date)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS day_medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entry_date TEXT NOT NULL,
                description TEXT NOT NULL,
                relief TEXT CHECK (relief IN ('yes', 'no', 'a_little'))
            )
        """)
        # Описание еды ограничено 50 символами также на уровне SQLite.
        # CAN CHANGE TEXT / LIMIT: при смене лимита потребуется миграция существующей таблицы meals.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entry_date TEXT NOT NULL,
                meal_time TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                utc_offset INTEGER NOT NULL,
                comment TEXT NOT NULL DEFAULT '' CHECK (length(comment) <= 50)
            )
        """)
        # Описание боли добавляется без изменения прежних ответов и шкал.
        await db.execute('''CREATE TABLE IF NOT EXISTS day_pain_answers (
            user_id INTEGER NOT NULL, entry_date TEXT NOT NULL, question_key TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('in_progress','answered','none','unknown','skipped')),
            updated_at INTEGER NOT NULL,
            PRIMARY KEY (user_id, entry_date, question_key))''')
        await db.execute('''CREATE TABLE IF NOT EXISTS day_pain_options (
            user_id INTEGER NOT NULL, entry_date TEXT NOT NULL, question_key TEXT NOT NULL,
            option_code TEXT NOT NULL, custom_text TEXT,
            is_selected INTEGER NOT NULL CHECK (is_selected IN (0,1)), updated_at INTEGER NOT NULL,
            PRIMARY KEY (user_id, entry_date, question_key, option_code))''')
        await db.execute("CREATE INDEX IF NOT EXISTS meals_user_date ON meals (user_id, entry_date, created_at)")
        async with db.execute("PRAGMA table_info(user_profiles)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
        if "last_reminder_at" not in columns:
            await db.execute("ALTER TABLE user_profiles ADD COLUMN last_reminder_at INTEGER")
        async with db.execute("PRAGMA table_info(diary_entries)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
        # Старые записи остаются без выдуманного времени; новые ответы получают UTC-время.
        if "updated_at" not in columns:
            await db.execute("ALTER TABLE diary_entries ADD COLUMN updated_at INTEGER")
        # Старый вопрос явно относил отход ко сну ко вчера: сохраняем это значение.
        if "bedtime_day" not in columns:
            await db.execute("ALTER TABLE diary_entries ADD COLUMN bedtime_day INTEGER NOT NULL DEFAULT -1 CHECK (bedtime_day IN (-1, 0))")
        await db.commit()


async def get_month_ratings(user_id: int, year: int, month: int) -> dict:
    first_day = date(year, month, 1).isoformat()
    last_day = date(year, month, calendar.monthrange(year, month)[1]).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT entry_date, sleep, food, mood
            FROM day_ratings
            WHERE user_id = ? AND entry_date BETWEEN ? AND ?
        """, (user_id, first_day, last_day)) as cursor:
            rows = await cursor.fetchall()
    ratings = {}
    for entry_date, sleep, food, mood in rows:
        ratings[entry_date] = {"sleep": sleep, "food": food, "mood": mood}
    return ratings


async def get_legacy_answer(user_id: int, selected_date: date) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT answer FROM calendar_answers
            WHERE user_id = ? AND entry_date = ?
        """, (user_id, selected_date.isoformat())) as cursor:
            row = await cursor.fetchone()
    if row is None:
        return None
    return row[0]


async def save_ratings(
    user_id: int, selected_date: date, sleep: int, food: int, mood: int
):
    async with aiosqlite.connect(DB_PATH) as db:
        # Один запрос и commit сохраняют все три оценки вместе.
        await db.execute("""
            INSERT INTO day_ratings (user_id, entry_date, sleep, food, mood)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, entry_date) DO UPDATE SET
                sleep = excluded.sleep,
                food = excluded.food,
                mood = excluded.mood
        """, (user_id, selected_date.isoformat(), sleep, food, mood))
        await db.execute(
            "UPDATE user_profiles SET last_entry_at = ? WHERE user_id = ?",
            (int(time()), user_id),
        )
        await db.commit()


async def ensure_user_profile(user_id: int, chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_profiles (user_id, chat_id) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET chat_id = excluded.chat_id, reminders_enabled = 1
        """, (user_id, chat_id))
        await db.commit()


async def get_user_profile(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)


async def save_profile_answer(user_id: int, field: str, value):
    # Имя столбца берём только из этого списка; пользовательский текст идёт параметром.
    fields = ("language", "nickname", "gender", "birth_year", "utc_offset", "reminder_period", "reminder_hour")
    if field not in fields:
        raise ValueError("Unknown profile field")
    async with aiosqlite.connect(DB_PATH) as db:
        if field == "reminder_hour":
            await db.execute("""
                UPDATE user_profiles SET reminder_hour = ?, setup_complete = 1,
                    reminder_started_at = ? WHERE user_id = ?
            """, (value, int(time()), user_id))
        else:
            await db.execute(f"UPDATE user_profiles SET {field} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()


async def reset_reminder_choice(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE user_profiles SET reminder_period = NULL, reminder_hour = NULL
            WHERE user_id = ? AND setup_complete = 0
        """, (user_id,))
        await db.commit()


async def get_reminder_profiles() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM user_profiles WHERE setup_complete = 1 AND reminders_enabled = 1
        """) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def reserve_reminder(user_id: int, local_date: str, inactive_before: int, expected_profile: dict | None = None) -> bool:
    expected = expected_profile or {}
    async with aiosqlite.connect(DB_PATH) as db:
        # Бронируем день до отправки, чтобы перезапуск не повторил напоминание.
        cursor = await db.execute("""
            UPDATE user_profiles SET last_reminder_date = ?, last_reminder_at = ?
            WHERE user_id = ? AND setup_complete = 1 AND reminders_enabled = 1
                AND (last_reminder_date IS NULL OR last_reminder_date != ?)
                AND COALESCE(last_entry_at, reminder_started_at) <= ?
                AND (? IS NULL OR (utc_offset = ? AND reminder_period = ? AND reminder_hour = ?))
        """, (
            local_date, inactive_before + 86400, user_id, local_date, inactive_before,
            expected.get("utc_offset"), expected.get("utc_offset"),
            expected.get("reminder_period"), expected.get("reminder_hour"),
        ))
        await db.commit()
        return cursor.rowcount == 1


async def disable_reminders(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE user_profiles SET reminders_enabled = 0 WHERE user_id = ?", (user_id,))
        await db.commit()


def reminder_date_after_timezone(profile: dict, new_offset: int, now: int):
    last_at = profile["last_reminder_at"]
    new_timezone = timezone(timedelta(hours=new_offset))
    if last_at is not None:
        return datetime.fromtimestamp(last_at, new_timezone).date().isoformat(), last_at
    old_timezone = timezone(timedelta(hours=profile["utc_offset"]))
    if profile["last_reminder_date"] == datetime.fromtimestamp(now, old_timezone).date().isoformat():
        # У прежних записей есть только дата: защищаем уже отмеченный день от дубля.
        return datetime.fromtimestamp(now, new_timezone).date().isoformat(), now
    return profile["last_reminder_date"], None


async def update_user_timezone(user_id: int, utc_offset: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Настройки и отметку уведомления меняем одной транзакцией.
        await db.execute("BEGIN IMMEDIATE")
        async with db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)) as cursor:
            profile = dict(await cursor.fetchone())
        reminder_date, reminder_at = reminder_date_after_timezone(profile, utc_offset, int(time()))
        await db.execute("""
            UPDATE user_profiles SET utc_offset = ?, last_reminder_date = ?, last_reminder_at = ?
            WHERE user_id = ?
        """, (utc_offset, reminder_date, reminder_at, user_id))
        await db.commit()


async def save_profile_settings(user_id: int, answers: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("BEGIN IMMEDIATE")
        async with db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)) as cursor:
            profile = dict(await cursor.fetchone())
        reminder_date, reminder_at = reminder_date_after_timezone(profile, answers["utc_offset"], int(time()))
        await db.execute("""
            UPDATE user_profiles SET language = ?, nickname = ?, gender = ?, birth_year = ?,
                utc_offset = ?, reminder_period = ?, reminder_hour = ?,
                last_reminder_date = ?, last_reminder_at = ? WHERE user_id = ?
        """, (
            # Отключённых полей нет в черновике: сохраняем прежние значения.
            answers["language"], answers["nickname"],
            answers.get("gender", profile["gender"]), answers.get("birth_year", profile["birth_year"]),
            answers["utc_offset"], answers["reminder_period"], answers["reminder_hour"],
            reminder_date, reminder_at, user_id,
        ))
        await db.commit()
