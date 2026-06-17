from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from src.bot.states import RegistrationStates, BookingStates, NightBookingStates, ProfileStates, BonusStates
from src.bot.keyboards.common import (
    get_main_client_keyboard,
    get_confirm_keyboard,
    get_back_keyboard,
    get_cancel_keyboard
)
from src.bot.keyboards.client import (
    get_month_keyboard,
    get_date_keyboard,
    get_engineer_keyboard,
    get_time_keyboard,
    get_duration_keyboard
)
from src.bot.database import async_session
from src.models.user import User
from src.models.booking import Booking, BookingStatus
from src.models.schedule import Schedule
from src.models.day_off import DayOff
from datetime import datetime, timedelta
import calendar
from sqlalchemy import select

router = Router()

# Helper function to get engineer info
async def get_engineers(session):
    result = await session.execute(
        select(User).where(User.role == "engineer", User.is_active == True)
    )
    return result.scalars().all()

# Helper function to get free time slots for an engineer on a given date
async def get_free_slots(engineer_id, date):
    # This is a simplified version; in reality, we'd check bookings and schedule
    # For now, return all slots from 11:00 to 22:00 every 30 minutes
    slots = []
    start_time = datetime.strptime("11:00", "%H:%M").time()
    end_time = datetime.strptime("22:00", "%H:%M").time()
    current = datetime.combine(date, start_time)
    end = datetime.combine(date, end_time)
    while current < end:
        slots.append(current.time())
        current += timedelta(minutes=30)
    return slots

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать в студию звукозаписи!\n"
        "Выберите действие:",
        reply_markup=get_main_client_keyboard()
    )

@router.message(F.text == "Записаться")
async def btn_record(message: Message, state: FSMContext):
    await state.set_state(BookingStates.choosing_month)
    # Show month selection
    await message.answer(
        "Выберите месяц:",
        reply_markup=get_month_keyboard()
    )

# Month selection handler
@router.callback_query(F.data.startswith("month:"), BookingStates.choosing_month)
async def process_month(callback: CallbackQuery, state: FSMContext):
    month = int(callback.data.split(":")[1])
    await state.update_data(month=month)
    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=get_date_keyboard(month)
    )
    await callback.answer()

# Date selection handler
@router.callback_query(F.data.startswith("date:"), BookingStates.choosing_date)
async def process_date(callback: CallbackQuery, state: FSMContext):
    day = int(callback.data.split(":")[1])
    data = await state.get_data()
    month = data["month"]
    year = datetime.now().year  # Simplified; could be next month if current month passed
    await state.update_data(day=day, month=month, year=year)
    await state.set_state(BookingStates.choosing_engineer)
    await callback.message.edit_text(
        "Выберите звукорежиссера:",
        reply_markup=get_engineer_keyboard()  # This should be dynamic from DB
    )
    await callback.answer()

# Engineer selection handler
@router.callback_query(F.data.startswith("engineer:"), BookingStates.choosing_engineer)
async def process_engineer(callback: CallbackQuery, state: FSMContext):
    engineer_id = int(callback.data.split(":")[1])
    await state.update_data(engineer_id=engineer_id)
    await state.set_state(BookingStates.choosing_time)
    data = await state.get_data()
    year = data["year"]
    month = data["month"]
    day = data["day"]
    date = datetime(year, month, day).date()
    # Get free slots for this engineer on this date
    # For now, we'll use a helper function
    # slots = await get_free_slots(engineer_id, date)
    # We'll show a keyboard with slots
    await callback.message.edit_text(
        "Выберите время:",
        reply_markup=get_time_keyboard()  # Simplified; should be dynamic
    )
    await callback.answer()

# Time selection handler
@router.callback_query(F.data.startswith("time:"), BookingStates.choosing_time)
async def process_time(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.split(":")[1]
    await state.update_data(time=time_str)
    await state.set_state(BookingStates.choosing_duration)
    await callback.message.edit_text(
        "Выберите продолжительность записи:",
        reply_markup=get_duration_keyboard()
    )
    await callback.answer()

# Duration selection handler
@router.callback_query(F.data.startswith("duration:"), BookingStates.choosing_duration)
async def process_duration(callback: CallbackQuery, state: FSMContext):
    duration = int(callback.data.split(":")[1])
    await state.update_data(duration=duration)
    await state.set_state(BookingStates.entering_name)
    await callback.message.edit_text(
        "Введите ваше имя:"
    )
    await callback.answer()
    # We'll send a new message for text input
    await callback.message.answer(
        "Введите ваше имя:",
        reply_markup=get_cancel_keyboard()
    )

# Name input handler
@router.message(BookingStates.entering_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingStates.entering_phone)
    await message.answer(
        f"Вы ввели имя: {message.text}\n"
        "Теперь отправьте ваш номер телефона через кнопку ниже или вручную:",
        reply_markup=get_contact_keyboard()  # We'll define this below
    )

# Phone input handler (we'll handle both contact and text)
@router.message(BookingStates.entering_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await show_confirmation(message, state)

@router.message(BookingStates.entering_phone)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)
    await show_confirmation(message, state)

async def show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    # Calculate total price (we'd need engineer's hourly rate)
    # For now, placeholder
    total_price = data["duration"] * 1000  # placeholder
    text = (
        f"Проверьте детали записи:\n"
        f"Дата: {data['day']:02d}.{data['month']:02d}.{data['year']}\n"
        f"Время: {data['time']}\n"
        f"Продолжительность: {data['duration']} час(а)\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Стоимость: {total_price} руб.\n"
    )
    await message.answer(
        text,
        reply_markup=get_confirm_keyboard()
    )

# Confirmation handler
@router.callback_query(F.data == "confirm", BookingStates.entering_phone)
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # Save booking to DB
    async with async_session() as session:
        # Get engineer to calculate price
        engineer = await session.get(User, data["engineer_id"])
        hourly_rate = engineer.hourly_rate if engineer and engineer.hourly_rate else 1000
        total_price = data["duration"] * hourly_rate
        booking = Booking(
            client_id=callback.from_user.id,  # This is telegram_id, we need to map to user id
            engineer_id=data["engineer_id"],
            start_time=datetime(
                data["year"], data["month"], data["day"],
                hour=int(data["time"].split(":")[0]),
                minute=int(data["time"].split(":")[1])
            ),
            duration_hours=data["duration"],
            status=BookingStatus.PENDING if data["duration"] <= 2 else BookingStatus.PENDING,  # For >=3 hours, it's pending admin/engineer confirmation
            is_night_booking=False,  # Simplified
            total_price=total_price
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
    await state.clear()
    await callback.message.edit_text(
        "Запись создана! Ожидайте подтверждения.",
        reply_markup=get_main_client_keyboard()
    )
    # Notify engineer if duration <= 2 hours
    if data["duration"] <= 2:
        # TODO: send notification to engineer
        pass
    else:
        # TODO: send notification to admin and engineer for manual confirmation
        pass
    await callback.answer()

# Edit and cancel handlers
@router.callback_query(F.data == "edit", BookingStates.entering_phone)
async def process_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.entering_name)
    await callback.message.edit_text(
        "Введите ваше имя:"
    )
    await callback.message.answer(
        "Введите ваше имя:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel", BookingStates.entering_phone)
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Запись отменена.",
        reply_markup=get_main_client_keyboard()
    )
    await callback.answer()

# Contact keyboard for phone input
def get_contact_keyboard():
    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
    builder = ReplyKeyboardBuilder()
    builder.button(text="Отправить номер", request_contact=True)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

# Other client handlers (My recordings, Bonuses, etc.) would go here