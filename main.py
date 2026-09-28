import asyncio
import logging
from maxapi import Bot, Dispatcher

from config import MAX_BOT_TOKEN
from db import init_db
from handlers import register_handlers

logging.basicConfig(level=logging.INFO)

bot = Bot(token=MAX_BOT_TOKEN)
dp = Dispatcher()

register_handlers(dp)


async def main():
    init_db()
    print("Bot started. DB initialized.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
