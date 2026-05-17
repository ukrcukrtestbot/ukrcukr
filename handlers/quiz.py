"""FSM-тест: 7 питань → проміжна заглушка."""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import texts
from states import Quiz

router = Router()

QUIZ_STATES = [Quiz.q1, Quiz.q2, Quiz.q3, Quiz.q4, Quiz.q5, Quiz.q6, Quiz.q7]


def _compute_result(answers: list[dict]) -> tuple[str, int, int]:
    """CUKR≥3 → A. UKR>CUKR → B. Інше → C. (q7_c — тай-брейкер до CUKR при рівному рахунку.)"""
    cukr = sum(a["score"].get("cukr", 0) for a in answers)
    ukr = sum(a["score"].get("ukr", 0) for a in answers)
    if cukr >= 3:
        return "A", cukr, ukr
    if ukr > cukr:
        return "B", cukr, ukr
    q7 = next((a for a in answers if a["q"] == 7), None)
    if cukr == ukr and q7 and q7["cb"] == "q7_c":
        return "A", cukr, ukr
    return "C", cukr, ukr


_RESULT_TEXTS = {
    "A": texts.RESULT_A_CUKR,
    "B": texts.RESULT_B_UKR,
    "C": texts.RESULT_C_BORDERLINE,
}


def _contact_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=texts.BTN_LEAVE_CONTACT,
                callback_data="collect_contact",
            ),
            InlineKeyboardButton(
                text=texts.BTN_RESTART_QUIZ,
                callback_data="restart_quiz",
            ),
        ]]
    )


def _keyboard(idx: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=cb_data)]
        for label, cb_data, _ in texts.QUESTIONS[idx]["options"]
    ]
    rows.append([
        InlineKeyboardButton(
            text=texts.BTN_RESTART_INLINE,
            callback_data="restart_quiz",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _text(idx: int) -> str:
    return texts.QUESTION_HEADER.format(n=idx + 1) + texts.QUESTIONS[idx]["text"]


async def _send_question(message: Message, state: FSMContext, idx: int):
    await state.set_state(QUIZ_STATES[idx])
    await message.answer(_text(idx), reply_markup=_keyboard(idx))


@router.callback_query(F.data == "start_quiz")
async def on_start_quiz(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup(reply_markup=None)
    await state.set_data({"answers": []})
    await _send_question(cb.message, state, 0)
    await cb.answer()


async def _handle_answer(cb: CallbackQuery, state: FSMContext, idx: int):
    options = texts.QUESTIONS[idx]["options"]
    selected = next((o for o in options if o[1] == cb.data), None)
    if selected is None:
        await cb.answer()
        return

    label, cb_data, score = selected
    await cb.message.edit_reply_markup(reply_markup=None)

    data = await state.get_data()
    answers = data.get("answers", [])
    answers.append({"q": idx + 1, "cb": cb_data, "label": label, "score": score})
    await state.update_data(answers=answers)

    if idx + 1 < len(QUIZ_STATES):
        await _send_question(cb.message, state, idx + 1)
    else:
        await _finish_quiz(cb, state)
    await cb.answer()


async def _finish_quiz(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    answers = data.get("answers", [])
    result, cukr, ukr = _compute_result(answers)
    await state.update_data(result=result, score_cukr=cukr, score_ukr=ukr)
    await state.set_state(None)
    await cb.message.answer(
        _RESULT_TEXTS[result],
        reply_markup=_contact_keyboard(),
    )


def _make_handler(idx: int):
    async def handler(cb: CallbackQuery, state: FSMContext):
        await _handle_answer(cb, state, idx)
    return handler


for _i, _st in enumerate(QUIZ_STATES):
    router.callback_query.register(
        _make_handler(_i), _st, F.data.startswith(f"q{_i + 1}_")
    )


# Якщо під час тесту користувач пише текст замість натиску кнопки —
# нагадуємо обрати варіант і не ламаємо FSM.
@router.message(Quiz.q1)
@router.message(Quiz.q2)
@router.message(Quiz.q3)
@router.message(Quiz.q4)
@router.message(Quiz.q5)
@router.message(Quiz.q6)
@router.message(Quiz.q7)
async def on_text_during_quiz(message: Message, state: FSMContext):
    current = await state.get_state()
    idx = next(
        (i for i, s in enumerate(QUIZ_STATES) if s.state == current), None
    )
    if idx is None:
        return
    await message.answer(
        texts.QUIZ_FALLBACK + "\n\n" + _text(idx),
        reply_markup=_keyboard(idx),
    )
