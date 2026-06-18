from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from src.bot.states import RegistrationStates, BookingStates, NightBookingStates, ProfileStates, BonusStates
from src.bot.keyboards.common import (
    get_main_client_keyboard,
    get_confirm_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
    get_main_admin_keyboard
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
from src.bot.config import Config
from sqlalchemy import select, or_, func
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Helper function to get engineer info (includes admins)
async def get_engineers(session):
    result = await session.execute(
        select(User).where(
            or_(User.role == "engineer", User.is_admin == True),
            User.is_active == True
        )
    )
    return result.scalars().all()

# Helper function to get free time slots for an engineer on a given date
async def get_free_slots(engineer_id, date):
    # Returns list of datetime.time objects representing free 30-minute slots
    async with async_session() as session:
        # Check day off
        dayoff = await session.execute(
            select(DayOff).where(
                DayOff.engineer_id == engineer_id,
                func.date(DayOff.date) == date
            )
        )
        if dayoff.scalar_one_or_none():
            return []  # engineer has day off

        # Get schedule for this day of week (Monday=0)
        weekday = date.weekday()  # 0 Monday
        schedule = await session.execute(
            select(Schedule).where(
                Schedule.engineer_id == engineer_id,
                Schedule.day_of_week == weekday,
                Schedule.is_active == True
            )
        )
        schedule_obj = schedule.scalar_one_or_none()
        if not schedule_obj:
            return []  # no schedule for this day

        # Determine work intervals, subtract break
        work_start = schedule_obj.start_time
        work_end = schedule_obj.end_time
        break_start = schedule_obj.break_start_time
        break_end = schedule_obj.break_end_time

        # Generate all possible slots within work hours (30 min steps)
        all_slots = []
        current_dt = datetime.combine(date, work_start)
        end_dt = datetime.combine(date, work_end)
        while current_dt < end_dt:
            slot_start = current_dt.time()
            slot_end_dt = current_dt + timedelta(minutes=30)
            slot_end = slot_end_dt.time()
            # If break exists and slot intersects break, skip
            if break_start and break_end:
                # slot range [slot_start, slot_end) intersects break [break_start, break_end)
                if not (slot_end <= break_start or slot_start >= break_end):
                    # overlap with break, skip
                    current_dt = slot_end_dt
                    continue
            all_slots.append((slot_start, slot_end))
            current_dt = slot_end_dt

        # Get existing bookings for this engineer on this date that are not cancelled
        bookings = await session.execute(
            select(Booking).where(
                Booking.engineer_id == engineer_id,
                func.date(Booking.start_time) == date,
                Booking.status.in_([
                    BookingStatus.PENDING,
                    BookingStatus.CONFIRMED,
                    BookingStatus.COMPLETED
                ])
            )
        )
        bookings_list = bookings.scalars().all()

        # Filter out slots that overlap with any booking
        free_slots = []
        for slot_start, slot_end in all_slots:
            slot_start_dt = datetime.combine(date, slot_start)
            slot_end_dt = datetime.combine(date, slot_end)
            overlap = False
            for b in bookings_list:
                b_start = b.start_time
                b_end = b.start_time + timedelta(hours=b.duration_hours)
                # Check overlap: not (slot_end <= b_start or slot_start >= b_end)
                if not (slot_end_dt <= b_start or slot_start_dt >= b_end):
                    overlap = True
                    break
            if not overlap:
                free_slots.append(slot_start)  # we only need start time for display

        return free_slots

async def notify_new_booking(bot, booking: Booking):
    """Send notification about new booking to engineer and admins."""
    async with async_session() as session:
        engineer = await session.get(User, booking.engineer_id)
        client = await session.get(User, booking.client_id)
        if not engineer or not client:
            return
        text = (
            f"Новая заявка на запись!\n"
            f"Клиент: {client.first_name} {client.last_name or ''} (@{client.username or 'нет_username'})\n"
            f"Дата: {booking.start_time.strftime('%d.%m.%Y %H:%M')}\n"
            f"Продолжительность: {booking.duration_hours} час(а)\n"
            f"Стоимость: {booking.total_price} руб.\n"
        )
        # Notify engineer
        try:
            await bot.send_message(engineer.telegram_id, text)
        except Exception:
            pass
        # Notify admins from config
        from src.bot.config import Config
        for admin_id in Config.ADMIN_IDS:
            try:
                await bot.send_message(admin_id, f"[Админ-уведомление] {text}")
            except Exception:
                pass

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать в студию звукозаписи!\n"
        "Выберите действие:",
        reply_markup=get_main_client_keyboard()
    )

@router.message(F.text == "/admin")
async def cmd_admin(message: Message, state: FSMContext):
    from src.bot.config import Config
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет доступа к админ-панели.")
        return
    await message.answer(
        "Админ-панель:",
        reply_markup=get_main_admin_keyboard()
    )

@router.message(F.text == "Ночная запись")
async def btn_night_record(message: Message, state: FSMContext):
    await state.set_state(BookingStates.choosing_month)
    await state.update_data(is_night_booking=True)
    await message.answer(
        "Выберите месяц для ночной записи:",
        reply_markup=get_month_keyboard()
    )

@router.message(F.text == "Наша команда")
async def btn_our_team(message: Message, state: FSMContext):
    await message.answer(
        "Наша команда звукорежиссеров:\n"
        "• Иванов Иван (ведущий инженер)\n"
        "• Петр Петров (запись и микс)\n"
        "• Сидорова Анна (мастеринг)\n"
        "Вы можете выбрать любого из них при записи.",
        reply_markup=get_main_client_keyboard()
    )

@router.message(F.text == "Мои записи")
async def btn_my_bookings(message: Message, state: FSMContext):
    await message.answer(
        "Функция «Мои записи» пока в разработке.\n"
        "Скоро вы сможете просматривать свои прошлые и upcoming записи.",
        reply_markup=get_main_client_keyboard()
    )

@router.message(F.text == "Бонусы и рефералы")
async def btn_bonus_referral(message: Message, state: FSMContext):
    await message.answer(
        "Бонусная система:\n"
        "• За каждую потраченную 1000 руб. вы получаете 100 бонусных баллов.\n"
        "• За каждого друга, записавшегося по вашей реферальной ссылке, вы получаете 500 баллов.\n"
        "Бонусы можно использовать для оплаты до 30% стоимости записи.\n"
        "Подробная информация скоро будет доступна.",
        reply_markup=get_main_client_keyboard()
    )

@router.message(F.text == "Контакты студии")
async def btn_contacts(message: Message, state: FSMContext):
    await message.answer(
        "Контакты студии звукозаписи:\n"
        "📍 Адрес: ул. Музыкальная, д. 10, г. Москва\n"
        "📞 Телефон: +7 (495) 123-45-67\n"
        "📧 Email: info@studio.example\n"
        "🕒 Часы работы: Пн‑Пт 11:00‑22:00, Сб‑Вс 12:00‑20:00\n"
        "Мы всегда рады видеть вас!",
        reply_markup=get_main_client_keyboard()
    )

@router.message(F.text == "Помощь")
async def btn_help(message: Message, state: FSMContext):
    await message.answer(
        "Помощь по использованию бота:\n"
        "1. Нажмите «Записаться» чтобы забронировать сеанс.\n"
        "2. Выберите месяц, дату, инженера, время и продолжительность.\n"
        "3. Введите имя и отправьте номер телефона.\n"
        "4. Подтвердите запись.\n"
        "5. Для ночной записи используйте кнопку «Ночная запись».\n"
        "6. Администраторы могут использовать команду /admin для доступа к панели управления.\n"
        "Если у вас остались вопросы, напишите нам в контакты студии.",
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
    free_slots = await get_free_slots(engineer_id, date)
    if not free_slots:
        await callback.message.edit_text(
            "На выбранную дату у этого инженера нет свободных слотов. Выберите другую дату или инженера.",
            reply_markup=get_date_keyboard(month)
        )
        await state.set_state(BookingStates.choosing_date)
        await callback.answer()
        return
    # Build keyboard with free slots
    builder = InlineKeyboardBuilder()
    for slot in free_slots:
        builder.button(text=slot.strftime("%H:%M"), callback_data=f"time:{slot.strftime('%H:%M')}")
    builder.button(text="🔙 Назад", callback_data="back_to_date")
    builder.adjust(4, 1)
    await callback.message.edit_text(
        "Выберите время:",
        reply_markup=builder.as_markup()
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

# Back handlers
@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_main_client_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_month")
async def back_to_month(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.choosing_month)
    await callback.message.edit_text(
        "Выберите месяц:",
        reply_markup=get_month_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_date")
async def back_to_date(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    month = data.get("month")
    if month is None:
        month = datetime.now().month
    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=get_date_keyboard(month)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_engineer")
async def back_to_engineer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    year = data.get("year", datetime.now().year)
    month = data.get("month", datetime.now().month)
    day = data.get("day", datetime.now().day)
    await state.set_state(BookingStates.choosing_engineer)
    await callback.message.edit_text(
        "Выберите звукорежиссера:",
        reply_markup=get_engineer_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_time")
async def back_to_time(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    engineer_id = data.get("engineer_id")
    year = data.get("year", datetime.now().year)
    month = data.get("month", datetime.now().month)
    day = data.get("day", datetime.now().day)
    date = datetime(year, month, day).date()
    # In real implementation, we'd compute free slots; for now just show time keyboard
    await state.set_state(BookingStates.choosing_time)
    await callback.message.edit_text(
        "Выберите время:",
        reply_markup=get_time_keyboard()
    )
    await callback.answer()

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
    async with async_session() as session:
        # Get or create client user
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        client_user = result.scalar_one_or_none()
        if not client_user:
            client_user = User(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
                role="client",
                is_active=True
            )
            session.add(client_user)
            await session.flush()  # to get id
        # Get engineer to calculate price
        engineer = await session.get(User, data["engineer_id"])
        if not engineer:
            await callback.answer("Инженер не найден.", show_alert=True)
            return
        hourly_rate = engineer.hourly_rate if engineer and engineer.hourly_rate else 1000
        total_price = data["duration"] * hourly_rate
        booking = Booking(
            client_id=client_user.id,
            engineer_id=data["engineer_id"],
            start_time=datetime(
                data["year"], data["month"], data["day"],
                hour=int(data["time"].split(":")[0]),
                minute=int(data["time"].split(":")[1])
            ),
            duration_hours=data["duration"],
            status=BookingStatus.PENDING,  # All new bookings start as PENDING; later engineer/admin can confirm
            is_night_booking=data.get("is_night_booking", False),
            total_price=total_price
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        # Notify engineer and admins about new booking
        await notify_new_booking(callback.bot, booking)
    await state.clear()
    await callback.message.edit_text(
        "Запись создана! Ожидайте подтверждения.",
        reply_markup=get_main_client_keyboard()
    )
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
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()
    builder.button(text="Отправить номер", request_contact=True)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

# Other client handlers (My recordings, Bonuses, etc.) would go here