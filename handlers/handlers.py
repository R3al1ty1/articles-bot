import asyncio
from pathlib import Path
import aiohttp
import os
import shutil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram_dialog import DialogManager
from aiogram.types import FSInputFile, InputMediaDocument
from aiogram.exceptions import AiogramError
from loguru import logger

from utils.formatter import format_sessions_message
from utils.payments import buy_session, check_payment_status, get_minutes_amount
from utils.consts import AMOUNTS_DCT
from database.requests import add_session_to_user, deduct_session, get_user_sessions, add_new_user
from dialogs import dialogs
from utils.tasks import cleanup_session, process_files, schedule_send_files
from utils.utils import get_files, send_files_message


router = Router()


articles_button = InlineKeyboardButton(text='Получить доступ', callback_data='articles_button_pressed')
keyboard = InlineKeyboardMarkup(inline_keyboard=[[articles_button]])

button_10 = InlineKeyboardButton(text='10 минут', callback_data='button_10')
button_15 = InlineKeyboardButton(text='15 минут', callback_data='button_15')
button_30 = InlineKeyboardButton(text='30 минут', callback_data='button_30')
button_hour = InlineKeyboardButton(text='1 час', callback_data='button_hour')

keyboard_payments = InlineKeyboardMarkup(inline_keyboard=[
    [button_15],
    # [button_hour]
])


@router.message(Command(commands='start'))
async def process_start_command(message: Message):
    """Обработчик команды /start."""
    username = str(message.chat.username)
    tg_id = message.from_user.id
    add_new_user(username, tg_id)
    image_path = Path(__file__).parent.parent / "opensci.jpg"
    photo = FSInputFile(image_path)
    await message.answer_photo(
        photo=photo,
        caption="Привет! 👋 Этот бот поможет вам легко и быстро получить доступ к функционалу Скопус.\n\nВоспользуйтесь кнопкой ниже или введите /access.\n\n📝 Продолжая, вы подтверждаете, что ознакомились с инструкцией: https://telegra.ph/Kak-ispolzovat-OpenSciBot-07-09\n\n🎉 Поздравляем! Вам начислено 2 пробные сессии по 15 минут!",
        reply_markup=keyboard
    )


@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    """Обработчик команды /help."""
    await message.answer(text="""
/access   - подключиться к сессии
/payments - пополнение баланса
/support  - связь с поддержкой
/balance  - баланс
"""
    )


@router.message(Command(commands='payments'))
async def process_payments_command(message: Message):
    """Обработчик команды /payments."""
    await message.answer(
        text="""💰 Выберите, пожалуйста, длительность сессии для покупки:

Доступ на 15 минут -  219 руб
""",
        reply_markup=keyboard_payments
    )


@router.callback_query(F.data.in_(['button_10', 'button_15', 'button_30', 'button_hour']))
async def generate_payment(callback: CallbackQuery):
    """Формирование платежа и его проверки."""
    amount = AMOUNTS_DCT[callback.data]
    payment_url, payment_id = buy_session(amount, callback.message.chat.id)
    url = InlineKeyboardButton(text="Оплата", url=payment_url)
    check = InlineKeyboardButton(text="Проверить оплату", callback_data=f'check_{payment_id}')
    keyboard_buy = InlineKeyboardMarkup(inline_keyboard=[[url, check]])

    await callback.message.answer(text="🔗 Ваша ссылка на оплату готова!\nПосле оплаты нажмите кнопку проверки платежа.",
                         reply_markup=keyboard_buy)


@router.callback_query(lambda x: "check" in x.data)
async def check_payment(callback: CallbackQuery):
    """Кнопка проверки платежа."""
    res = check_payment_status(callback.data.split('_')[-1])
    mins = get_minutes_amount(callback.data.split('_')[-1])
    if res:
        add_session_to_user(tg_id=int(callback.from_user.id), length=int(mins), count=1)
        await callback.message.answer(f"✅ Оплата успешно завершена, на баланс зачислен доступ на {mins} минут.")
    else:
        await callback.message.answer("⌛️ Оплата еще не прошла.")


@router.message(Command(commands='support'))
async def process_support_command(message: Message):
    """Обработчик команды /support."""
    await message.answer(text="💬 Поддержка: @chadbugsy\n📝 Инструкция: https://telegra.ph/Kak-ispolzovat-OpenSciBot-07-09")


@router.message(Command(commands='balance'))
async def process_balance_command(message: Message):
    tg_id = message.from_user.id
    sessions = get_user_sessions(tg_id)
    if sessions:
        await message.answer(format_sessions_message(sessions))
    else:
        await message.answer(f"У вас нет купленных доступов.\n💳 Чтобы пополнить баланс, используйте команду /payments.")


@router.callback_query(F.data == "articles_button_pressed", StateFilter(default_state))
async def process_articles_button(callback: CallbackQuery, state: FSMContext):
    username = str(callback.message.chat.username)
    tg_id = callback.from_user.id
    add_new_user(username, tg_id)
    
    user_sessions = get_user_sessions(tg_id)
    
    if user_sessions:
        await state.update_data(user_sessions=user_sessions)

        keyboard = dialogs.create_session_keyboard(user_sessions)

        await callback.message.answer("Выберите длительность сессии:", reply_markup=keyboard)

        await state.set_state(dialogs.SessionStates.selecting_session)
    else:
        await callback.message.answer("К сожалению, на вашем балансе закончились сессии.\nПриобретите их сейчас👇🏼")
        await process_payments_command(callback.message)
    
    await callback.answer()


@router.message(Command(commands='access'))
async def process_access_command(message: Message, state: FSMContext):
    username = str(message.chat.username)
    tg_id = message.from_user.id
    add_new_user(username, tg_id)
    
    user_sessions = get_user_sessions(tg_id)
    
    if user_sessions:
        await state.update_data(user_sessions=user_sessions)

        keyboard = dialogs.create_session_keyboard(user_sessions)

        await message.answer("Выберите длительность сессии:", reply_markup=keyboard)

        await state.set_state(dialogs.SessionStates.selecting_session)
    else:
        await message.answer("К сожалению, на вашем балансе закончились сессии.\nПриобретите их сейчас👇🏼")
        await process_payments_command(message)
        return


@router.callback_query(dialogs.SessionCallbackFactory.filter(F.action == "select"), dialogs.SessionStates.selecting_session)
async def process_session_selection(callback: CallbackQuery, callback_data: dialogs.SessionCallbackFactory, state: FSMContext):
    session_length = callback_data.length

    await state.update_data(selected_length=session_length)

    keyboard = dialogs.create_confirmation_keyboard(session_length)

    session_names = {10: '10 минут', 15: '15 минут', 30: '30 минут', 60: '1 час'}
    session_name = session_names.get(session_length, f"{session_length} минут")

    await callback.message.edit_text(
        f"Вы выбрали сессию длительностью {session_name}. Вы уверены?", 
        reply_markup=keyboard
    )

    await state.set_state(dialogs.SessionStates.confirming_session)

    await callback.answer()


@router.callback_query(dialogs.SessionCallbackFactory.filter(F.action == "confirm"), dialogs.SessionStates.confirming_session)
async def process_session_confirmation(callback: CallbackQuery, callback_data: dialogs.SessionCallbackFactory, state: FSMContext):
    data = await state.get_data()
    session_length = data.get("selected_length")
    user_id = callback.from_user.id

    session_names = {10: '10 минут', 15: '15 минут', 30: '30 минут', 60: '1 час'}
    session_name = session_names.get(session_length, f"{session_length} минут")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://opensci.ru/create/{user_id}",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status() 
                
                result = await response.json()

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📥 Получить файлы", 
                        callback_data=dialogs.SessionCallbackFactory(action="download", length=0).pack()
                    )]
                ])

                if result.get('status') == 'created':
                    deduct_session(tg_id=user_id, length=session_length)
                    cleanup_session.apply_async(args=[str(user_id)], countdown=session_length * 60)
                    asyncio.create_task(schedule_send_files(session_length, str(user_id), callback))

                    message = (f"✅ Сессия длительностью {session_name} успешно начата!\n\n"
                               f"🔗 Ссылка для доступа: {result['access_url']}")
                elif result.get('status') == 'exists':
                    message = (f"❗️ Обнаружена активная сессия!\n\n"
                               f"🔗 Ссылка для доступа: {result['access_url']}")
                else:
                    message = "🤔 Произошла неизвестная ошибка при создании сессии. Пожалуйста, попробуйте снова."
                await asyncio.sleep(2)
                await callback.message.edit_text(
                    text=message,
                    reply_markup=keyboard
                )

    except aiohttp.ClientResponseError as e:
        if e.status == 429:
            try:
                error_details = await e.json()
                error_message = error_details.get('detail', "Сервис перегружен. Попробуйте через 15 минут.")
            except Exception:
                error_message = "Сервис временно перегружен. Пожалуйста, попробуйте через 15 минут."
            
            await callback.message.edit_text(f"⚠️ {error_message}")
        else:
            await callback.message.edit_text(f"⚠️ Ошибка сервера сессий. Попробуйте позже.")
        logger.warning(f"HTTP Response Error for user {user_id}: {e.status} - {e.message}")

    except aiohttp.ClientError as e:
        await callback.message.edit_text("⚠️ Ошибка соединения с сервером сессий. Пожалуйста, попробуйте позже.")
        logger.error(f"Client connection error for user {user_id}: {str(e)}")

    except AiogramError as e:
        await callback.message.edit_text("⚠️ Ошибка при обработке сообщения. Попробуйте снова.")
        logger.error(f"Telegram API error for user {user_id}: {str(e)}")
    except Exception as e:
        await callback.message.edit_text(f"⚠️ Непредвиденная ошибка. Сообщите в поддержку.")
        logger.critical(f"Unexpected error in session confirmation for user {user_id}: {str(e)}", exc_info=True)

    finally:
        await state.clear()
        await callback.answer()


@router.callback_query(dialogs.SessionCallbackFactory.filter(F.action == "download"))
async def process_files_download(callback: CallbackQuery, callback_data: dialogs.SessionCallbackFactory, state: FSMContext):
    temp_dir = None
    temp_zip_path = None
    try:
        user_id = callback.from_user.id
        await callback.answer("Загрузка файлов...")
        files = await get_files(user_id)
        await send_files_message(files, callback)

    except Exception as e:
        await callback.message.answer(f"❌ Файлы не найдены.")
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        if temp_zip_path:
            os.remove(temp_zip_path)
        await callback.answer()


@router.callback_query(dialogs.SessionCallbackFactory.filter(F.action == "back"), dialogs.SessionStates.confirming_session)
async def process_session_back(callback: CallbackQuery, callback_data: dialogs.SessionCallbackFactory, state: FSMContext):
    data = await state.get_data()
    user_sessions = data.get("user_sessions")

    if not user_sessions:
        tg_id = callback.from_user.id
        user_sessions = get_user_sessions(tg_id)
    
    if user_sessions:
        keyboard = dialogs.create_session_keyboard(user_sessions)
        await callback.message.edit_text("Выберите длительность сессии:", reply_markup=keyboard)
        await state.update_data(user_sessions=user_sessions)
        await state.set_state(dialogs.SessionStates.selecting_session)
    else:
        await callback.message.edit_text("К сожалению, на вашем балансе закончились сессии.")
        await process_payments_command(callback.message)

    await callback.answer()
