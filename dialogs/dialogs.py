from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from typing import Optional


class SessionStates(StatesGroup):
    selecting_session = State()
    selecting_website = State()
    confirming_session = State()

class SessionCallbackFactory(CallbackData, prefix="session"):
    action: str
    length: Optional[int] = None
    website: Optional[str] = None


def create_session_keyboard(user_sessions):
    session_names = {
        10: '10 минут',
        15: '15 минут',
        30: '30 минут',
        60: '1 час'
    }

    available_buttons = []

    for session in user_sessions:
        session_length = session.length
        session_count = session.count
        
        if session_length in session_names:
            button = InlineKeyboardButton(
                text=f'{session_names[session_length]} ({session_count})', 
                callback_data=SessionCallbackFactory(action="select_length", length=session_length).pack()
            )
            available_buttons.append(button)

    keyboard_rows = []
    row = []
    
    for i, button in enumerate(available_buttons):
        row.append(button)
        if len(row) == 2 or i == len(available_buttons) - 1:
            keyboard_rows.append(row)
            row = []
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


def create_website_keyboard():
    scopus_button = InlineKeyboardButton(
        text="Scopus",
        callback_data=SessionCallbackFactory(action="select_website", website="scopus").pack()
    )
    # wos_button = InlineKeyboardButton(
    #     text="Web of Science",
    #     callback_data=SessionCallbackFactory(action="select_website", website="wos").pack()
    # )
    
    return InlineKeyboardMarkup(inline_keyboard=[[scopus_button]])


def create_confirmation_keyboard(session_length, website):
    confirm_button = InlineKeyboardButton(
        text="Да, уверен", 
        callback_data=SessionCallbackFactory(action="confirm", length=session_length, website=website).pack()
    )
    back_button = InlineKeyboardButton(
        text="Вернуться к выбору", 
        callback_data=SessionCallbackFactory(action="back_to_website_selection").pack()
    )
    
    return InlineKeyboardMarkup(inline_keyboard=[[confirm_button], [back_button]])