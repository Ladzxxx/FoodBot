from datetime import date, timedelta
from secrets import token_hex

import aiosqlite

import database
from day_storage import get_day_entry

SLEEP_STEPS = ("bedtime", "wake_time", "sleep_satisfaction")


def sleep_complete(entry):
    return all((entry or {}).get(field) is not None for field in SLEEP_STEPS)


def other_complete(entry):
    return bool((entry or {}).get("day_section_complete") or (entry or {}).get("completed"))


async def morning_entry_needed(user_id, sleep_date):
    sleep = await get_day_entry(user_id, sleep_date)
    other = await get_day_entry(user_id, sleep_date - timedelta(days=1))
    return not sleep_complete(sleep) or not other_complete(other)


async def get_morning_session(user_id):
    async with aiosqlite.connect(database.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall("SELECT * FROM morning_sessions WHERE user_id = ?", (user_id,))
    return dict(rows[0]) if rows else None


async def start_morning_session(user_id, sleep_date, mode, utc_offset):
    session = {
        "user_id": user_id, "sleep_date": sleep_date.isoformat(),
        "other_date": (sleep_date - timedelta(days=1)).isoformat(),
        "session_id": token_hex(6), "step": "bedtime",
        "edit_sleep": int(mode == "sleep"), "edit_other": int(mode == "other"),
        "utc_offset": utc_offset,
    }
    async with aiosqlite.connect(database.DB_PATH) as db:
        await db.execute("""INSERT INTO morning_sessions
            (user_id, sleep_date, other_date, session_id, step, edit_sleep, edit_other, utc_offset)
            VALUES (:user_id, :sleep_date, :other_date, :session_id, :step, :edit_sleep, :edit_other, :utc_offset)
            ON CONFLICT(user_id) DO UPDATE SET sleep_date = excluded.sleep_date,
            other_date = excluded.other_date, session_id = excluded.session_id,
            step = excluded.step, edit_sleep = excluded.edit_sleep,
            edit_other = excluded.edit_other, utc_offset = excluded.utc_offset, answers_count = 0""", session)
        await db.commit()
    return session


async def set_morning_step(user_id, session_id, step):
    async with aiosqlite.connect(database.DB_PATH) as db:
        await db.execute("UPDATE morning_sessions SET step = ? WHERE user_id = ? AND session_id = ?",
            (step, user_id, session_id))
        await db.commit()


async def first_other_step(session):
    entry = await get_day_entry(session["user_id"], date.fromisoformat(session["other_date"])) or {}
    if session["edit_other"]:
        return "mood_control"
    if other_complete(entry):
        return "complete"
    step = entry.get("next_step", "mood_control")
    return step if step not in (*SLEEP_STEPS, "complete") else "mood_control"


async def next_morning_step(session, proposed):
    if proposed not in SLEEP_STEPS:
        if proposed != "complete" and not session["edit_other"]:
            # За время паузы день могли заполнить вручную через календарь.
            return await first_other_step(session)
        return proposed
    entry = await get_day_entry(session["user_id"], date.fromisoformat(session["sleep_date"])) or {}
    for step in SLEEP_STEPS[SLEEP_STEPS.index(proposed):]:
        if session["edit_sleep"] or entry.get(step) is None:
            return step
    return await first_other_step(session)


def morning_date(session, step):
    return date.fromisoformat(session["sleep_date"] if step in SLEEP_STEPS else session["other_date"])


async def finish_morning_session(user_id, session_id):
    # Таймер меняется только при реально сохранённых ответах, не при просмотре заполненных блоков.
    async with aiosqlite.connect(database.DB_PATH) as db:
        rows = await db.execute_fetchall(
            "SELECT answers_count FROM morning_sessions WHERE user_id = ? AND session_id = ?", (user_id, session_id))
        cursor = await db.execute(
            "DELETE FROM morning_sessions WHERE user_id = ? AND session_id = ?", (user_id, session_id))
        if cursor.rowcount and rows and rows[0][0] > 0:
            from time import time
            await db.execute("UPDATE user_profiles SET last_entry_at = ? WHERE user_id = ?", (int(time()), user_id))
        await db.commit()
