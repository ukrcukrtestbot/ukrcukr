"""Збір контактів: імʼя → телефон → місто → фінал."""
import logging
import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

import config
import lead
import texts
from states import Contact

router = Router()
log = logging.getLogger("contact")

PHONE_RE = re.compile(r"^\+(48|380)\d{9}$")


# --- клавіатури ---

def _phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.BTN_SHARE_CONTACT, request_contact=True)],
            [KeyboardButton(text=texts.BTN_ENTER_PHONE_MANUALLY)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _city_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(texts.CITIES), 2):
        row = [
            InlineKeyboardButton(text=c, callback_data=f"city:{c}")
            for c in texts.CITIES[i : i + 2]
        ]
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text=texts.BTN_OTHER_CITY, callback_data="city:other")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- вхід у флоу ---

@router.callback_query(F.data == "collect_contact")
async def on_collect_contact(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await state.set_state(Contact.name)
    await cb.message.answer(texts.ASK_NAME)
    await cb.answer()


# --- крок 1: імʼя ---

@router.message(Contact.name, F.text)
async def on_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not (2 <= len(name) <= 40) or name.isdigit():
        await message.answer(texts.NAME_INVALID)
        return
    await state.update_data(name=name)
    await state.set_state(Contact.phone)
    await message.answer(
        texts.ASK_PHONE.format(name=name),
        reply_markup=_phone_keyboard(),
    )


# --- крок 2: телефон ---

@router.message(Contact.phone, F.contact)
async def on_phone_shared(message: Message, state: FSMContext):
    log.info("on_phone_shared fired, contact=%s", message.contact)
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await _save_phone_and_ask_city(message, state, phone)


@router.message(Contact.phone, F.text == texts.BTN_ENTER_PHONE_MANUALLY)
async def on_phone_manual_choice(message: Message, state: FSMContext):
    await state.set_state(Contact.phone_manual)
    await message.answer(texts.ASK_PHONE_MANUAL, reply_markup=ReplyKeyboardRemove())


@router.message(Contact.phone)
async def on_phone_other(message: Message, state: FSMContext):
    # Якщо людина почала писати номер замість натиску кнопки — пробуємо валідувати.
    await _try_manual_phone(message, state)


@router.message(Contact.phone_manual)
async def on_phone_manual(message: Message, state: FSMContext):
    await _try_manual_phone(message, state)


async def _try_manual_phone(message: Message, state: FSMContext):
    text = (message.text or "").strip().replace(" ", "")
    if not PHONE_RE.match(text):
        await message.answer(texts.PHONE_INVALID)
        return
    await _save_phone_and_ask_city(message, state, text)


async def _save_phone_and_ask_city(message: Message, state: FSMContext, phone: str):
    log.info("phone saved: %s -> ask city", phone)
    await state.update_data(phone=phone)
    await state.set_state(Contact.city)
    await message.answer(texts.ASK_CITY, reply_markup=_city_keyboard())


# --- крок 3: місто ---

@router.callback_query(Contact.city, F.data.startswith("city:"))
async def on_city(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    value = cb.data.split(":", 1)[1]
    if value == "other":
        await state.set_state(Contact.city_manual)
        await cb.message.answer(texts.ASK_CITY_MANUAL)
    else:
        await _finish(cb.message, state, value)
    await cb.answer()


@router.message(Contact.city_manual, F.text)
async def on_city_manual(message: Message, state: FSMContext):
    city = (message.text or "").strip()
    if not (2 <= len(city) <= 60):
        await message.answer(texts.ASK_CITY_MANUAL)
        return
    await _finish(message, state, city)


async def _finish(message: Message, state: FSMContext, city: str):
    log.info("finishing: city=%s", city)
    await state.update_data(city=city)
    data = await state.get_data()
    await lead.send_lead(message.bot, data, message.from_user)
    await state.set_state(None)
    await message.answer(texts.CONTACT_DONE.format(manager=config.MANAGER_USERNAME))
