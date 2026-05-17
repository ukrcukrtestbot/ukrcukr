"""FSM-стани бота. Поки заготовка — заповнимо на наступних кроках."""
from aiogram.fsm.state import State, StatesGroup


class Quiz(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()
    q6 = State()
    q7 = State()


class Contact(StatesGroup):
    name = State()
    phone = State()           # очікуємо share-contact або «вручну»
    phone_manual = State()    # після натиску «вручну» — текстовий ввод
    city = State()            # очікуємо інлайн-кнопку міста або «інше»
    city_manual = State()     # після натиску «інше» — текстовий ввод
