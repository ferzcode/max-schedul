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

BASE_URL = "https://techrepublic-filing-sold-telephony.trycloudflare.com"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH


async def main():
    init_db()

    try:
        await bot.unsubscribe_webhook(url=BASE_URL)
        print("Removed old subscription")
    except Exception as e:
        print(f"No old subscription: {e}")

    try:
        await bot.unsubscribe_webhook(url=WEBHOOK_URL)
        print("Removed old subscription /webhook")
    except Exception as e:
        print(f"No old /webhook subscription: {e}")

    try:
        await bot.subscribe_webhook(url=WEBHOOK_URL)
        print(f"Webhook registered: {WEBHOOK_URL}")
    except Exception as e:
        print(f"Subscribe failed: {e}")
        return

    print("Server started on port 8080")
    await dp.handle_webhook(bot=bot, host="0.0.0.0", port=8080, path=WEBHOOK_PATH)


if __name__ == "__main__":
    asyncio.run(main())
