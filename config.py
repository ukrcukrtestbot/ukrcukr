"""Конфігурація бота — читає змінні з .env"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не знайдено. Перевір файл .env")

_mgr = os.getenv("MANAGER_CHAT_ID")
MANAGER_CHAT_ID = int(_mgr) if _mgr else None
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME", "manager")
