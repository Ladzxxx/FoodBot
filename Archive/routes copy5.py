import asyncio

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

subscribers = set()

async def notifier (bot: Bot):
    while True:
        if subscribers:
            for user_id in list(subscribers):
                try:
                    await bot.send_message(chat_id=user_id, text="This is a notification message.")
                except Exception:
                    pass
        await asyncio.sleep(60)  # Send notifications every 60 seconds

@router.message(Command("start"))
async def started(message: Message, state: FSMContext):
    await message.answer(
        "Hello! I am a sub bot and i can help you wiht getting news\n\n"
        "Commands:\n"
        "/sub - subscribe to news\n"
        "/unsub - unsubscribe from news\n"
        "/subs - list of all subscribers\n",
        parse_mode="HTML")

@router.message(Command("sub"))
async def subscribe(message: Message):
    user_id = message.from_user.id
    if user_id not in subscribers:
        subscribers.add(user_id)
        await message.answer("You have successfully subscribed to notifications.")
    else:
        await message.answer("You are already subscribed to notifications.")

@router.message(Command("unsub"))
async def unsubscribe(message: Message):
    user_id = message.from_user.id
    if user_id in subscribers:
        subscribers.remove(user_id)
        await message.answer("You have successfully unsubscribed from notifications.")
    else:
        await message.answer("You are not subscribed to notifications.")

@router.message(Command("subs"))
async def list_subscribers(message: Message):
    if subscribers:
        subscriber_list = "\n".join(str(user_id) for user_id in subscribers)
        await message.answer(f"List of subscribers:\n{subscriber_list}")
    else:
        await message.answer("There are no subscribers at the moment.")