"""Формування і відправка ліда менеджеру в Telegram."""
import html
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot

import config
import texts

log = logging.getLogger("lead")

WARSAW = ZoneInfo("Europe/Warsaw")


def _format_telegram(user) -> str:
    if user is None:
        return "—"
    if user.username:
        return f"@{html.escape(user.username)} (id: {user.id})"
    return f"id: {user.id}"


def _format_answers(answers: list[dict]) -> str:
    lines = []
    for a in answers:
        topic = texts.QUESTION_TOPICS[a["q"] - 1]
        lines.append(f"{a['q']}. {topic}: {html.escape(a['label'])}")
    return "\n".join(lines)


def build_lead_message(data: dict, user) -> str:
    answers = data.get("answers", [])
    utm = data.get("utm")
    return texts.LEAD_TEMPLATE.format(
        name=html.escape(data.get("name", "—")),
        phone=html.escape(data.get("phone", "—")),
        city=html.escape(data.get("city", "—")),
        time=datetime.now(WARSAW).strftime("%d.%m.%Y %H:%M"),
        recommendation=texts.RESULT_LABELS.get(data.get("result", ""), "—"),
        cukr=data.get("score_cukr", 0),
        ukr=data.get("score_ukr", 0),
        answers=_format_answers(answers),
        utm=html.escape(utm) if utm else "direct",
        telegram=_format_telegram(user),
    )


async def send_lead(bot: Bot, data: dict, user) -> bool:
    if not config.MANAGER_CHAT_ID:
        log.warning("MANAGER_CHAT_ID не заданий — лід нікому не надіслано")
        return False
    text = build_lead_message(data, user)
    try:
        await bot.send_message(config.MANAGER_CHAT_ID, text)
        log.info("lead sent to %s", config.MANAGER_CHAT_ID)
        return True
    except Exception as e:
        log.exception("failed to send lead: %s", e)
        return False
