"""Обробники /start і /help."""
from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config
import texts

router = Router()


def _start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=texts.BTN_START_QUIZ,
                callback_data="start_quiz",
            )
        ]]
    )


def _welcome_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=texts.BTN_RESTART_QUIZ, callback_data="restart_quiz",
            )],
            [InlineKeyboardButton(
                text=texts.BTN_LEAVE_CONTACT, callback_data="collect_contact",
            )],
        ]
    )


@router.message(CommandStart())
async def on_start(message: Message, command: CommandObject, state: FSMContext):
    utm = (command.args or "").strip() or None
    data = await state.get_data()
    if data.get("result"):
        # Тест уже пройдено — показуємо коротке меню повернення.
        await state.set_state(None)
        if utm:
            await state.update_data(utm=utm)
        await message.answer(texts.WELCOME_BACK, reply_markup=_welcome_back_keyboard())
        return
    await state.clear()
    if utm:
        await state.update_data(utm=utm)
    await message.answer(texts.WELCOME, reply_markup=_start_keyboard())


@router.callback_query(F.data == "restart_quiz")
async def on_restart_quiz(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await state.clear()
    await cb.message.answer(texts.WELCOME, reply_markup=_start_keyboard())
    await cb.answer()


@router.message(Command("help"))
async def on_help(message: Message):
    await message.answer(texts.HELP_TEXT.format(manager=config.MANAGER_USERNAME))
