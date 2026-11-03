from os import getenv
from pathlib import Path
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import SimpleEventIsolation
from dotenv import load_dotenv

from database import init_db
from Handlers.routes import router as calendar_router
from Handlers.day import router as day_router
from Handlers.statistics import router as statistics_router
from Handlers.profile import router as profile_router
from Handlers.meal import router as meal_router
from Handlers.commands import router as commands_router, set_bot_commands
from reminders import reminder_loop
from Handlers.pain import router as pain_router

# Нажатия одного пользователя идут по очереди: двойной клик не пропустит вопрос.
dispatcher = Dispatcher(events_isolation=SimpleEventIsolation())

dispatcher.include_routers(calendar_router, commands_router, pain_router, day_router, statistics_router, meal_router, profile_router)


async def main():
    load_dotenv(Path(__file__).with_name(".env"))
    token = getenv("BOT_TOKEN")
    if not token:
        # CAN CHANGE TEXT
        raise RuntimeError("Укажите BOT_TOKEN в файле .env в корне проекта.")

    await init_db()
    bot = Bot(token=token)

    # CAN CHANGE TEXT
    print("Бот запускается...")
    reminder_task = None
    try:
        await set_bot_commands(bot)
        reminder_task = asyncio.create_task(reminder_loop(bot))
        await dispatcher.start_polling(bot, close_bot_session=False)
    finally:
        # Останавливаем напоминания до закрытия соединения с Telegram.
        if reminder_task is not None:
            reminder_task.cancel()
            await asyncio.gather(reminder_task, return_exceptions=True)
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
