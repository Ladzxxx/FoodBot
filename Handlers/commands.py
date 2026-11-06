from localization import t, language_of
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeChat, MenuButtonCommands, Message

from Keyboards.profile import commands_keyboard
from database import get_user_profile

router = Router()

# CAN CHANGE TEXT: команды и описания в меню Telegram.
BOT_COMMANDS = [
    BotCommand(command="makenote", description="📝 Open your diary and recent entries"),
    BotCommand(command="callendar", description="📅 Open the calendar; keep unfinished notes"),
    BotCommand(command="meal", description="🍽 Record a meal now"),
    BotCommand(command="statistics", description="📊 All-time and monthly statistics"),
    BotCommand(command="settings", description="⚙️ Set up your profile again"),
    BotCommand(command="timezone", description="🌍 Change your time zone"),
    BotCommand(command="start", description="🏠 Restart the conversation and open the calendar"),
    BotCommand(command="help", description="❓ How to use Foodie"),
    BotCommand(command="privacy", description="Privacy policy"),
    BotCommand(command="delete_me", description="Delete my data"),
    BotCommand(command="language", description="🌐 Change interface language"),
]

async def set_bot_commands(bot: Bot):
    await bot.set_my_commands(commands_for("ru"))
    for language in ("ru", "en"):
        await bot.set_my_commands(commands_for(language), language_code=language)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())


def commands_for(lang):
    return [BotCommand(command=item.command, description=t(lang, "command." + item.command)) for item in BOT_COMMANDS]


async def set_chat_commands(bot, chat_id, lang):
    # Явный выбор имеет приоритет над языком клиента Telegram.
    await bot.set_my_commands(commands_for(lang), scope=BotCommandScopeChat(chat_id=chat_id))


async def show_reply_menu(message: Message, lang="en"):
    # Reply- и inline-клавиатуру нельзя передать в одном сообщении.
    # CAN CHANGE TEXT: короткое сообщение устанавливает постоянное меню команд.
    await message.answer(t(lang, 'commands.quick_commands'), reply_markup=commands_keyboard())


@router.message(Command("help"))
async def help_command(message: Message):
    language_profile = await get_user_profile(message.from_user.id) if message.from_user else None
    lang = language_of(language_profile)
    await message.answer(t(lang, "commands.help"), reply_markup=commands_keyboard())
