from time import time

import aiosqlite

import database

POLICY_VERSION = "2026-11-06"
CONSENT_VERSION = "2026-11-06"

# Только незавершённые попытки удаления, не список отказавшихся пользователей.
# Успешное удаление убирает ID; ошибка отзыва в БД закрывает доступ и в памяти.
pending_deletions = set()

# Только таблицы приложения; имена не принимаются из Telegram.
USER_TABLES = (
    "day_pain_options", "day_pain_answers", "day_medications", "meals",
    "diary_entries", "calendar_answers", "day_ratings", "morning_sessions",
    "user_consents", "user_profiles",
)


async def has_consent(user_id):
    if user_id in pending_deletions:
        return False
    async with aiosqlite.connect(database.DB_PATH) as db:
        rows = await db.execute_fetchall(
            "SELECT 1 FROM user_consents WHERE user_id = ? AND policy_version = ? AND consent_version = ?",
            (user_id, POLICY_VERSION, CONSENT_VERSION),
        )
    return bool(rows)


async def accept_consent(user_id, lang):
    async with aiosqlite.connect(database.DB_PATH) as db:
        await db.execute("""INSERT INTO user_consents
            (user_id, policy_version, consent_version, accepted_at, language)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET policy_version = excluded.policy_version,
            consent_version = excluded.consent_version, accepted_at = excluded.accepted_at,
            language = excluded.language""",
            (user_id, POLICY_VERSION, CONSENT_VERSION, int(time()), lang))
        await db.commit()


async def delete_user_data(user_id):
    pending_deletions.add(user_id)
    # Сначала отзываем доступ отдельной транзакцией. Если удаление не удастся,
    # оставшиеся записи не станут доступны и напоминания не возобновятся.
    async with aiosqlite.connect(database.DB_PATH) as db:
        await db.execute("DELETE FROM user_consents WHERE user_id = ?", (user_id,))
        await db.execute("UPDATE user_profiles SET reminders_enabled = 0 WHERE user_id = ?", (user_id,))
        await db.commit()
    async with aiosqlite.connect(database.DB_PATH) as db:
        await db.execute("BEGIN IMMEDIATE")
        # Не пропускаем новую неизвестную таблицу с user_id при будущем расширении.
        rows = await db.execute_fetchall("SELECT name FROM sqlite_master WHERE type = 'table'")
        for (table,) in rows:
            # Имена пришли из SQLite; кавычки защищают PRAGMA.
            quoted = '"' + table.replace('"', '""') + '"'
            columns = await db.execute_fetchall(f"PRAGMA table_info({quoted})")
            if any(column[1] == "user_id" for column in columns) and table not in USER_TABLES:
                raise RuntimeError("Add the new user table to the deletion list")
        for table in USER_TABLES:
            await db.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
        await db.commit()

    pending_deletions.discard(user_id)
