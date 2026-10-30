from os import getenv
import asyncio
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
from Handlers.routes import notifier, router

load_dotenv()

token = getenv("BOT_TOKEN")

dispatcher = Dispatcher()

dispatcher.include_router(router)

async def main():
    bot = Bot(token=token)

    asyncio.create_task(notifier(bot))

    print("Bot is starting...")
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())