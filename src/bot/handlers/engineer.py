from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from src.bot.states import BookingStates  # We might need engineer-specific states
from src.bot.keyboards.common import get_main_engineer_keyboard, get_confirm_keyboard, get_back_keyboard
from src.bot.keyboards.engineer import (
    get_new_requests_keyboard,
    get_request_details_keyboard
)
from src.bot.database import async_session
from src.models.user import User
from src.models.booking import Booking, BookingStatus
from datetime import datetime
from sqlalchemy import select

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать, звукорежиссер!\n"
        "Выберите действие:",
        reply_markup=get_main_engineer_keyboard()
    )

@router.message(F.text == "Новые заявки")
async def btn_new_requests(message: Message, state: FSMContext):
    # Get pending bookings for this engineer
    async with async_session() as session:
        engineer = await session.get(User, message.from_user.id)  # Simplified: assuming telegram_id matches user id
        if not engineer:
            await message.answer("Вы не зарегистрированы как звукорежиссер.")
            return
        bookings = await session.execute(
            select(Booking).where(
                Booking.engineer_id == engineer.id,
                Booking.status == BookingStatus.PENDING
            ).order_by(Booking.start_time)
        )
        bookings = bookings.scalars().all()
    if not bookings:
        await message.answer("Новых заявок нет.")
        return
    await message.answer(
        "Новые заявки:",
        reply_markup=get_new_requests_keyboard(bookings)
    )

# Handler for selecting a specific request
@router.callback_query(F.data.startswith("request:"))
async def process_request(callback: CallbackQuery, state: FSMContext):
    booking_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Заявка не найдена.")
            return
        # Get client info
        client = await session.get(User, booking.client_id)
    text = (
        f"Заявка #{booking.id}\n"
        f"Клиент: {client.first_name} {client.last_name or ''}\n"
        f"Телефон: {client.phone_number}\n"
        f"Дата: {booking.start_time.strftime('%d.%m.%Y')}\n"
        f"Время: {booking.start_time.strftime('%H:%M')}\n"
        f"Продолжительность: {booking.duration_hours} час(а)\n"
        f"Стоимость: {booking.total_price} руб.\n"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_request_details_keyboard(booking.id)
    )
    await callback.answer()

# Handler for confirming a request (for durations <= 2 hours)
@router.callback_query(F.data.startswith("confirm_request:"))
async def process_confirm_request(callback: CallbackQuery, state: FSMContext):
    booking_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Заявка не найдена.")
            return
        booking.status = BookingStatus.CONFIRMED
        await session.commit()
    await callback.message.edit_text(
        f"Заявка #{booking.id} подтверждена.",
        reply_markup=get_main_engineer_keyboard()
    )
    # Notify client
    # TODO: send notification to client
    await callback.answer()

# Handler for rejecting a request
@router.callback_query(F.data.startswith("reject_request:"))
async def process_reject_request(callback: CallbackQuery, state: FSMContext):
    booking_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            await callback.answer("Заявка не найдена.")
            return
        booking.status = BookingStatus.REJECTED
        await session.commit()
    await callback.message.edit_text(
        f"Заявка #{booking.id} отклонена.",
        reply_markup=get_main_engineer_keyboard()
    )
    # Notify client with reason (we'd need to ask for reason)
    # TODO: ask for reason and send to client
    await callback.answer()

# Placeholder for other engineer handlers (My recordings, Schedule, etc.)
# ...
