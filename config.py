import os
from dotenv import load_dotenv

load_dotenv()

MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not MAX_BOT_TOKEN:
    raise ValueError("MAX_BOT_TOKEN не задан в .env")
