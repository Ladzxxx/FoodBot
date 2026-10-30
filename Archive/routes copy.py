from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, 
    KeyboardButton, 
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

router = Router()
count = 0


def start_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть сайт", url="https://www.youtube.com/watch?v=EWhlCUgbOr8")],
            [InlineKeyboardButton(text="Помощь", callback_data="Help")],
            [InlineKeyboardButton(text="Обо мне", callback_data="About_me"), InlineKeyboardButton(text="Пингануть", callback_data="Ping")]
        ]
    )
    return keyboard

def about_me_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Как меня зовут?", callback_data="my_name"), InlineKeyboardButton(text="Мой Telegram", callback_data="my_telegram")],
            [InlineKeyboardButton(text="Сколько пингов", callback_data="count"), InlineKeyboardButton(text="Пингануть", callback_data="Ping")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )
    return keyboard

@router.message(Command(commands=["start"]))
@router.message(F.text.lower() == "старт")
async def start(message: Message):
    await message.answer(
        "*Hello!* _I'm your friendly bot!_ \n\nUse /help for assistance or press a button below to get started.",
        parse_mode="markdown", 
        reply_markup=start_keyboard())

@router.callback_query(lambda c: c.data == "Help")
async def help_me_callback(callback: CallbackQuery):
    await callback.message.answer("This bot is created using aiogram. It responds to commands and messages. Use /help to see available commands or /about to learn about the bot.")
    await callback.answer()

@router.callback_query(lambda c: c.data == "About_me")
async def about_me_callback(callback: CallbackQuery):
    await callback.message.answer(
        f"What do you want to know about yourself?",
        parse_mode="markdown",
        reply_markup=about_me_keyboard())
    await callback.answer()

@router.callback_query(lambda c: c.data == "Ping")
async def ping_callback(callback: CallbackQuery):
    global count
    count += 1
    await callback.message.answer(f"You pinged me! <i>I'm alive and well.</i> <b>Ping count:</b> {count}", parse_mode="HTML")
    await callback.answer()

@router.callback_query(lambda c: c.data == "my_name")
async def my_name_callback(callback: CallbackQuery):
    await callback.message.answer(
        f"Your name is {callback.from_user.full_name}",
        parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(lambda c: c.data == "my_telegram") 
async def my_telegram_callback(callback: CallbackQuery):
    await callback.message.answer(
        f"Your username is @{callback.from_user.username} and Your ID is {callback.from_user.id}",
        parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(lambda c: c.data == "count") 
async def counted_callback(callback: CallbackQuery):
    await callback.message.answer(
        f"Your Count is {count}",
        parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(lambda c: c.data == "back")
async def start_callback(callback: CallbackQuery):
    await callback.message.answer(
        f"*Hello!* _I'm your friendly bot!_ \n\nUse /help for assistance or press a button below to get started.",
        parse_mode="markdown",
        reply_markup=start_keyboard()
        )
    await callback.answer()

@router.message(Command(commands=["help"]))
@router.message(F.text.lower() == "помощь")
async def help(message: Message):
    await message.answer(
        f"This is a help message. \n\nUse /ping to check if it's alive.\nUse /about to learn more about yourself.",
        parse_mode="markdown",
        )

@router.message(Command(commands=["count"]))
@router.message(F.text.lower() == "посчитать")
async def show_count(message: Message):
    if count > 10:
        await message.answer(
            f"Thats a big count! ;) \n\n<b>Ping count:</b> {count}",
            parse_mode="HTML"
            )
    else:
        await message.answer(
            f"Thats a small count :( \n\n<b>Ping count:</b> {count}",
            parse_mode="HTML")

@router.message(F.text.lower() == "я тебя люблю")
async def love_reply(message: Message):
    await message.answer("I love you too! ❤️")

@router.message()
async def fallback(message: Message):
    await message.answer("I don't understand that. If you are stuck use /start or use /help for assistance.")
