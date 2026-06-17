from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from src.bot.states import AdminStates
from src.bot.keyboards.common import get_main_admin_keyboard, get_confirm_keyboard, get_back_keyboard
from src.bot.keyboards.admin import (
    get_clients_keyboard,
    get_client_details_keyboard,
    get_add_user_keyboard
)
from src.bot.database import async_session
from src.models.user import User
from src.models.booking import Booking
from src.models.bonus import BonusTransaction
from src.models.referral import Referral
from datetime import datetime, timedelta
from sqlalchemy import select

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать, администратор!\n"
        "Выберите действие:",
        reply_markup=get_main_admin_keyboard()
    )

@router.message(F.text == "Клиенты")
async def btn_clients(message: Message, state: FSMContext):
    await state.set_state(AdminStates.viewing_clients)
    async with async_session() as session:
        clients = await session.execute(
            select(User).where(User.role == "client", User.is_active == True)
        )
        clients = clients.scalars().all()
    await message.answer(
        "Список клиентов:",
        reply_markup=get_clients_keyboard(clients)
    )

@router.callback_query(F.data.startswith("client:"), AdminStates.viewing_clients)
async def process_client(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split(":")[1])
    await state.update_data(client_id=client_id)
    await state.set_state(AdminStates.viewing_client_details)
    async with async_session() as session:
        client = await session.get(User, client_id)
        # Get client's bookings
        bookings = await session.execute(
            select(Booking).where(Booking.client_id == client_id)
        )
        bookings = bookings.scalars().all()
        # Get bonus transactions
        bonuses = await session.execute(
            select(BonusTransaction).where(BonusTransaction.user_id == client_id)
        )
        bonuses = bonuses.scalars().all()
        # Get referrals
        referrals = await session.execute(
            select(Referral).where(Referral.referrer_id == client_id)
        )
        referrals = referrals.scalars().all()
    text = (
        f"Клиент: {client.first_name} {client.last_name or ''}\n"
        f"Username: @{client.username or 'не указан'}\n"
        f"Телефон: {client.phone_number or 'не указан'}\n"
        f"Дата регистрации: {client.registration_date.strftime('%d.%m.%Y')}\n"
        f"Всего записей: {len(bookings)}\n"
        f"Завершенных записей: {len([b for b in bookings if b.status == BookingStatus.COMPLETED])}\n"
        f"Отмен: {len([b for b in bookings if b.status == BookingStatus.CANCELLED_CLIENT])}\n"
        f"Рефералов: {len(referrals)}\n"
        f"Бонусных баллов: {sum(b.amount for b in bonuses if b.amount > 0)}\n"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_client_details_keyboard(client_id)
    )
    await callback.answer()

@router.message(F.text == "Добавить звукорежиссера")
async def btn_add_engineer(message: Message, state: FSMContext):
    await state.set_state(AdminStates.adding_engineer)
    await message.answer(
        "Введите Telegram ID пользователя, которого хотите назначить звукорежиссером:",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminStates.adding_engineer)
async def process_add_engineer(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text)
    except ValueError:
        await message.answer("Telegram ID должен быть числом. Попробуйте снова.")
        return
    async with async_session() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            # Create new user
            user = User(
                telegram_id=telegram_id,
                role="engineer",
                is_active=True
            )
            session.add(user)
        else:
            user.role = "engineer"
            user.is_active = True
        await session.commit()
        await session.refresh(user)
    await state.clear()
    await message.answer(
        f"Пользователь с Telegram ID {telegram_id} теперь является звукорежиссером.",
        reply_markup=get_main_admin_keyboard()
    )

# Similar handler for adding admin
@router.message(F.text == "Добавить администратора")
async def btn_add_admin(message: Message, state: FSMContext):
    await state.set_state(AdminStates.adding_admin)
    await message.answer(
        "Введите Telegram ID пользователя, которого хотите назначить администратором:",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminStates.adding_admin)
async def process_add_admin(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text)
    except ValueError:
        await message.answer("Telegram ID должен быть числом. Попробуйте снова.")
        return
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                role="admin",
                is_active=True
            )
            session.add(user)
        else:
            user.role = "admin"
            user.is_active = True
        await session.commit()
        await session.refresh(user)
    await state.clear()
    await message.answer(
        f"Пользователь с Telegram ID {telegram_id} теперь является администратором.",
        reply_markup=get_main_admin_keyboard()
    )

# Placeholder for other admin handlers (statistics, bookings, bonuses, etc.)
# ...
