import asyncio
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date, datetime, timezone
from html import unescape
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiosqlite
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import DeleteMessage, EditMessageText
from aiogram.types import CallbackQuery, Chat, Message, Update, User

import database
import main
from Forms.day import DayEdit
from day_storage import get_day_entry


def day_buttons(keyboard):
    return {
        button.callback_data.removeprefix("calendar:day:"): button.text
        for row in keyboard.inline_keyboard
        for button in row
        if button.callback_data.startswith("calendar:day:")
    }


def make_message(user_id=100, text=None, message_id=1, first_name="Tester"):
    return Message(
        message_id=message_id,
        date=datetime(2026, 10, 31, tzinfo=timezone.utc),
        chat=Chat(id=user_id, type="private"),
        from_user=User(id=user_id, is_bot=False, first_name=first_name),
        text=text,
    )


class BotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        db_path = Path(folder.name) / "calendar.sqlite3"
        db_patch = patch.object(database, "DB_PATH", db_path)
        db_patch.start()
        self.addCleanup(db_patch.stop)

        # Начинаем с настоящей схемы первого этапа и двух старых ответов.
        with closing(sqlite3.connect(db_path)) as db:
            db.execute("""
                CREATE TABLE calendar_answers (
                    user_id INTEGER NOT NULL,
                    entry_date TEXT NOT NULL,
                    answer INTEGER NOT NULL CHECK (answer IN (0, 1)),
                    PRIMARY KEY (user_id, entry_date)
                )
            """)
            db.executemany(
                "INSERT INTO calendar_answers VALUES (?, ?, ?)",
                [(100, "2024-02-10", 1), (100, "2024-02-11", 0)],
            )
            db.commit()
        await database.init_db()
        async with aiosqlite.connect(database.DB_PATH) as db:
            await db.execute("""
                INSERT INTO user_profiles (user_id, chat_id, language, nickname, gender, birth_year,
                    utc_offset, reminder_period, reminder_hour, setup_complete, reminder_started_at)
                VALUES (100, 100, 'en', 'Tester', 'secret', 2000, 0, 'morning', 9, 1, 0)
            """)
            await db.commit()

        self.bot = Bot(token="123456:TEST_TOKEN")
        self.addAsyncCleanup(self.bot.session.close)
        for user_id in (100, 200, 300):
            state = main.dispatcher.fsm.get_context(
                bot=self.bot, chat_id=user_id, user_id=user_id
            )
            await state.clear()
            self.addAsyncCleanup(state.clear)
        self.state = main.dispatcher.fsm.get_context(bot=self.bot, chat_id=100, user_id=100)

        self.message_events = []
        self.screens = {}
        self.current_message_id = 1
        self.next_message_id = 100
        for name, method, effect in [
            ("send", "answer", self.send_message),
            ("photo", "answer_photo", self.send_photo),
            ("document", "answer_document", self.send_document),
            ("edit", "edit_text", self.edit_message),
            ("delete", "delete", self.delete_message),
            ("edit_markup", "edit_reply_markup", self.edit_message_markup),
        ]:
            method_patch = patch.object(Message, method, autospec=True, side_effect=effect)
            setattr(self, name, method_patch.start())
            self.addCleanup(method_patch.stop)
        answer_patch = patch.object(CallbackQuery, "answer", new_callable=AsyncMock)
        self.acknowledge = answer_patch.start()
        self.addCleanup(answer_patch.stop)
        api_patch = patch.object(self.bot, "edit_message_text", new_callable=AsyncMock, side_effect=self.edit_message_by_id)
        self.api_edit = api_patch.start()
        self.addCleanup(api_patch.stop)
        markup_patch = patch.object(self.bot, "edit_message_reply_markup", new_callable=AsyncMock, side_effect=self.edit_markup_by_id)
        self.api_markup = markup_patch.start()
        self.addCleanup(markup_patch.stop)
        delete_patch = patch.object(self.bot, 'delete_message', new_callable=AsyncMock, side_effect=self.delete_by_id)
        self.api_delete = delete_patch.start()
        self.addCleanup(delete_patch.stop)
        for method in ("set_my_commands", "set_chat_menu_button"):
            command_patch = patch.object(self.bot, method, new_callable=AsyncMock, return_value=True)
            command_patch.start()
            self.addCleanup(command_patch.stop)

    async def send_message(self, message, text, **kwargs):
        self.next_message_id += 1
        sent = make_message(message.chat.id, text, self.next_message_id)
        self.message_events.append(("send", sent.message_id))
        self.screens[sent.message_id] = {"text": text, "keyboard": kwargs.get("reply_markup"), "parse_mode": kwargs.get("parse_mode")}
        self.current_message_id = sent.message_id
        return sent

    async def send_photo(self, message, photo, caption=None, **kwargs):
        sent = await self.send_message(message, caption or "", **kwargs)
        self.screens[sent.message_id]["photo"] = photo
        return sent

    async def send_document(self, message, document, caption=None, **kwargs):
        sent = await self.send_message(message, caption or "", **kwargs)
        self.screens[sent.message_id]["document"] = document
        return sent

    async def edit_message(self, message, text, **kwargs):
        self.screens[message.message_id] = {"text": text, "keyboard": kwargs.get("reply_markup"), "parse_mode": kwargs.get("parse_mode")}
        self.current_message_id = message.message_id
        return message

    async def edit_message_by_id(self, chat_id, message_id, text, reply_markup=None, parse_mode=None):
        self.screens[message_id] = {"text": text, "keyboard": reply_markup, "parse_mode": parse_mode}
        return make_message(chat_id, text=text, message_id=message_id)

    async def edit_markup_by_id(self, chat_id, message_id, reply_markup=None):
        if message_id in self.screens:
            self.screens[message_id]["keyboard"] = reply_markup
        return make_message(chat_id, message_id=message_id)

    async def delete_message(self, message):
        self.message_events.append(("delete", message.message_id))
        self.screens.pop(message.message_id, None)
        return True

    async def delete_by_id(self, chat_id, message_id):
        self.message_events.append(('delete', message_id))
        self.screens.pop(message_id, None)
        return True

    async def edit_message_markup(self, message, reply_markup=None):
        if message.message_id in self.screens:
            self.screens[message.message_id]["keyboard"] = reply_markup
        return message

    async def click(self, data, user_id=100, message_id=None):
        if message_id is None:
            message_id = self.current_message_id
        message = make_message(user_id, message_id=message_id)
        callback = CallbackQuery(
            id="test_callback", from_user=message.from_user,
            chat_instance="test_chat", message=message, data=data,
        )
        await main.dispatcher.feed_update(self.bot, Update(update_id=1, callback_query=callback))

    async def command(self, text, user_id=100, first_name="Tester"):
        message = make_message(user_id, text=text, first_name=first_name)
        await main.dispatcher.feed_update(self.bot, Update(update_id=1, message=message))

    def keyboard(self):
        return self.screens[self.current_message_id]["keyboard"]

    def screen_text(self):
        screen = self.screens[self.current_message_id]
        if screen.get("parse_mode") == "HTML":
            # Telegram показывает текст без служебных тегов; сохранённый HTML тоже доступен проверкам.
            return unescape(screen["text"].replace("<b>", "").replace("</b>", ""))
        return screen["text"]

    def button_data(self, text):
        for row in self.keyboard().inline_keyboard:
            for button in row:
                if button.text == text:
                    return button.callback_data
        self.fail(f"Button not found: {text}")

    async def read_day(self, day="2024-02-12", user_id=100):
        selected = date.fromisoformat(day)
        ratings = await database.get_month_ratings(user_id, selected.year, selected.month)
        return ratings.get(day, {})

    async def read_entry(self, day="2024-02-12", user_id=100):
        return await get_day_entry(user_id, date.fromisoformat(day))

    async def finish_edit(self, day="2024-02-12", values=(8, 7), user_id=100):
        if await database.get_user_profile(user_id) is None:
            await database.ensure_user_profile(user_id, user_id)
            await database.save_profile_answer(user_id, "language", "en")
        await self.open_day_edit(day, user_id)
        for label in ("21:00", "08:00", str(values[0]), str(values[1]), "No", "No"):
            await self.click(self.button_data(label), user_id=user_id)

    async def open_day_edit(self, day="2024-02-12", user_id=100):
        await self.click(f"day:edit:{day}", user_id=user_id)
        labels = [b.text for row in self.keyboard().inline_keyboard for b in row]
        if "Continue draft" in labels:
            await self.click(self.button_data("Continue draft"), user_id=user_id)
