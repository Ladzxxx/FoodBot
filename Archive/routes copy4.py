from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message, 
    KeyboardButton, 
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile
)
from Forms.user import Form
from aiogram.fsm.context import FSMContext
import aiohttp
import aiosqlite

router = Router()

# ----

DB_NAME = "market_bot_db.sql"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL
            )
        """)
        await db.commit()

async def add_user(name: str, age: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO users (name, age) VALUES (?, ?)", (name, age))
        await db.commit()

async def get_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users")
        result = await cursor.fetchall()
        return result
# ----

@router.message(Command("start"))
async def started(message: Message, state: FSMContext):
    await message.answer(f"Hello! Send a command /reg AGE to register your age. For example: /reg 25 ",
        parse_mode="HTML")

@router.message(Command("reg"))
async def register_user(message: Message, state: FSMContext):
    parts = message.text.strip().split(maxsplit=2)
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Invalid command format. Please use: /reg <age>")
        return

    await add_user(message.from_user.full_name, int(parts[1]))
    
    await message.answer(f"Everything is fine! Your age has been registered as {parts[1]}",
        parse_mode="HTML")

@router.message(Command("users"))
async def get_users_list(message: Message):
    users = await get_users()
    if not users:
        await message.answer("No users found.")
        return

    user_list = "\n".join([f"ID: {user[0]}, Name: {user[1]}, Age: {user[2]}" for user in users])

    await message.answer(f"Registered users:\n\n{user_list}",
        parse_mode="HTML")