"""Точка входу. Запуск: python bot.py"""
import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from handlers import contact, quiz, start
from storage import SqliteStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("bot")


async def main():
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = SqliteStorage(Path(__file__).parent / "state.db")
    dp = Dispatcher(storage=storage)
    dp.include_router(start.router)
    dp.include_router(quiz.router)
    dp.include_router(contact.router)

    me = await bot.get_me()
    log.info("Бот запущений: @%s (id=%s)", me.username, me.id)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Бот зупинений")
