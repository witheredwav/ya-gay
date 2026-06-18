from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.bot.states import AdminStates
from src.bot.keyboards.common import get_main_admin_keyboard, get_confirm_keyboard, get_back_keyboard
from src.bot.keyboards.admin import (
    get_clients_keyboard,
    get_client_details_keyboard,
    get_add_user_keyboard
)
from src.bot.database import async_session
from src.models.user import User
from src.models.booking import Booking, BookingStatus
from src.models.bonus import BonusTransaction
from src.models.referral import Referral
from datetime import datetime, timedelta
from sqlalchemy import select, func

# Inline keyboard for statistics menu
def get_statistics_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Заявки (Pending)", callback_data="stat_requests")
    builder.button(text="Подтвержденные записи", callback_data="stat_confirmed")
    builder.button(text="Отмены", callback_data="stat_cancellations")
    builder.button(text="Выручка", callback_data="stat_revenue")
    builder.adjust(1)
    return builder.as_markup()

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
                is_active=True,
                is_admin=False
            )
            session.add(user)
        else:
            user.role = "engineer"
            user.is_active = True
            user.is_admin = False
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
                is_active=True,
                is_admin=True
            )
            session.add(user)
        else:
            user.role = "admin"
            user.is_active = True
            user.is_admin = True
        await session.commit()
        await session.refresh(user)
    await state.clear()
    await message.answer(
        f"Пользователь с Telegram ID {telegram_id} теперь является администратором.",
        reply_markup=get_main_admin_keyboard()
    )

@router.callback_query(F.data.startswith("client_history:"))
async def process_client_history(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split(":")[1])
    await state.update_data(client_id=client_id)
    async with async_session() as session:
        bookings = await session.execute(
            select(Booking).where(Booking.client_id == client_id).order_by(Booking.start_time.desc())
        )
        bookings = bookings.scalars().all()
        if not bookings:
            text = "У клиента нет записей."
        else:
            text = "История записей:\n"
            for b in bookings:
                text += f"• {b.start_time.strftime('%d.%m.%Y %H:%M')} - {b.duration_hours}ч, статус: {b.status.value}\n"
    await callback.message.edit_text(
        text,
        reply_markup=get_client_details_keyboard(client_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("client_bonuses:"))
async def process_client_bonuses(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split(":")[1])
    await state.update_data(client_id=client_id)
    async with async_session() as session:
        bonuses = await session.execute(
            select(BonusTransaction).where(BonusTransaction.user_id == client_id).order_by(BonusTransaction.created_at.desc())
        )
        bonuses = bonuses.scalars().all()
        if not bonuses:
            text = "У клиента нет бонусных транзакций."
        else:
            text = "История бонусов:\n"
            for bt in bonuses:
                sign = "+" if bt.amount > 0 else ""
                text += f"• {bt.created_at.strftime('%d.%m.%Y')}: {sign}{bt.amount} ({bt.description or 'без описания'})\n"
    await callback.message.edit_text(
        text,
        reply_markup=get_client_details_keyboard(client_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("client_referrals:"))
async def process_client_referrals(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split(":")[1])
    await state.update_data(client_id=client_id)
    async with async_session() as session:
        referrals = await session.execute(
            select(Referral).where(Referral.referrer_id == client_id).order_by(Referral.created_at.desc())
        )
        referrals = referrals.scalars().all()
        if not referrals:
            text = "У клиента нет рефералов."
        else:
            text = "История рефералов:\n"
            for r in referrals:
                text += f"• {r.created_at.strftime('%d.%m.%Y')} - пригласил пользователя TG ID {r.referred_id}\n"
    await callback.message.edit_text(
        text,
        reply_markup=get_client_details_keyboard(client_id)
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_clients")
async def process_back_to_clients(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.viewing_clients)
    async with async_session() as session:
        clients = await session.execute(
            select(User).where(User.role == "client", User.is_active == True)
        )
        clients = clients.scalars().all()
    await callback.message.edit_text(
        "Список клиентов:",
        reply_markup=get_clients_keyboard(clients)
    )
    await callback.answer()

# Statistics handlers (placeholders)
@router.callback_query(F.data == "stat_requests")
async def process_stat_requests(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        # Count pending bookings
        pending = await session.execute(
            select(Booking).where(Booking.status == BookingStatus.PENDING)
        )
        pending_cnt = len(pending.scalars().all())
        # Count new requests? We'll treat pending as new requests
        text = f"Количество новых заявок (Pending): {pending_cnt}"
    await callback.message.edit_text(
        text,
        reply_markup=get_statistics_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "stat_confirmed")
async def process_stat_confirmed(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        confirmed = await session.execute(
            select(Booking).where(Booking.status == BookingStatus.CONFIRMED)
        )
        confirmed_cnt = len(confirmed.scalars().all())
        text = f"Подтвержденные записи: {confirmed_cnt}"
    await callback.message.edit_text(
        text,
        reply_markup=get_statistics_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "stat_cancellations")
async def process_stat_cancellations(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        cancelled = await session.execute(
            select(Booking).where(Booking.status.in_([BookingStatus.CANCELLED_CLIENT, BookingStatus.CANCELLED_ENGINEER]))
        )
        cancelled_cnt = len(cancelled.scalars().all())
        text = f"Отмены: {cancelled_cnt}"
    await callback.message.edit_text(
        text,
        reply_markup=get_statistics_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "stat_revenue")
async def process_stat_revenue(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        # Sum total_price of completed bookings
        result = await session.execute(
            select(func.sum(Booking.total_price)).where(Booking.status == BookingStatus.COMPLETED)
        )
        total = result.scalar_one() or 0
        text = f"Выручка (завершенные записи): {total} руб."
    await callback.message.edit_text(
        text,
        reply_markup=get_statistics_keyboard()
    )
    await callback.answer()

# New handlers for admin menu buttons
@router.message(F.text == "Статистика")
async def btn_statistics(message: Message, state: FSMContext):
    await message.answer(
        "Выберите тип статистики:",
        reply_markup=get_statistics_keyboard()
    )

@router.message(F.text == "Все записи")
async def btn_all_bookings(message: Message, state: FSMContext):
    async with async_session() as session:
        bookings = await session.execute(
            select(Booking).order_by(Booking.start_time.desc()).limit(20)
        )
        bookings = bookings.scalars().all()
        if not bookings:
            text = "Записей нет."
        else:
            text = "Все записи (последние 20):\n"
            for b in bookings:
                client = await session.get(User, b.client_id)
                engineer = await session.get(User, b.engineer_id)
                text += (
                    f"• {b.start_time.strftime('%d.%m.%Y %H:%M')} - "
                    f"Клиент: {client.first_name if client else '?'}, "
                    f"Инженер: {engineer.first_name if engineer else '?'}\n"
                    f"  Длительность: {b.duration_hours}ч, Статус: {b.status.value}, "
                    f"Стоимость: {b.total_price} руб.\n"
                )
    await message.answer(text)

@router.message(F.text == "Ночные записи")
async def btn_night_bookings(message: Message, state: FSMContext):
    async with async_session() as session:
        bookings = await session.execute(
            select(Booking)
            .where(Booking.is_night_booking == True)
            .order_by(Booking.start_time.desc())
            .limit(20)
        )
        bookings = bookings.scalars().all()
        if not bookings:
            text = "Ночных записей нет."
        else:
            text = "Ночные записи (последние 20):\n"
            for b in bookings:
                client = await session.get(User, b.client_id)
                engineer = await session.get(User, b.engineer_id)
                text += (
                    f"• {b.start_time.strftime('%d.%m.%Y %H:%M')} - "
                    f"Клиент: {client.first_name if client else '?'}, "
                    f"Инженер: {engineer.first_name if engineer else '?'}\n"
                    f"  Длительность: {b.duration_hours}ч, Статус: {b.status.value}, "
                    f"Стоимость: {b.total_price} руб.\n"
                )
    await message.answer(text)

@router.message(F.text == "Пользователи")
async def btn_all_users(message: Message, state: FSMContext):
    async with async_session() as session:
        users = await session.execute(
            select(User).order_by(User.registration_date.desc())
        )
        users = users.scalars().all()
        if not users:
            text = "Пользователей нет."
        else:
            text = "Пользователи:\n"
            for u in users:
                text += (
                    f"• ID: {u.id}, TG ID: {u.telegram_id}, "
                    f"Имя: {u.first_name or ''} {u.last_name or ''}, "
                    f"Роль: {u.role}, Активен: {u.is_active}\n"
                )
    await message.answer(text)

@router.message(F.text == "Звукорежиссеры")
async def btn_engineers(message: Message, state: FSMContext):
    async with async_session() as session:
        engineers = await session.execute(
            select(User).where(User.role == "engineer", User.is_active == True)
        )
        engineers = engineers.scalars().all()
        if not engineers:
            text = "Звукорежиссеров нет."
        else:
            text = "Звукорежиссеры:\n"
            for e in engineers:
                text += (
                    f"• ID: {e.id}, TG ID: {e.telegram_id}, "
                    f"Имя: {e.first_name or ''} {e.last_name or ''}, "
                    f"Ставка: {e.hourly_rate or 'не указана'} руб/ч\n"
                )
    await message.answer(text)

@router.message(F.text == "Администраторы")
async def btn_admins(message: Message, state: FSMContext):
    async with async_session() as session:
        admins = await session.execute(
            select(User).where(User.role == "admin", User.is_active == True)
        )
        admins = admins.scalars().all()
        if not admins:
            text = "Администраторов нет."
        else:
            text = "Администраторы:\n"
            for a in admins:
                text += (
                    f"• ID: {a.id}, TG ID: {a.telegram_id}, "
                    f"Имя: {a.first_name or ''} {a.last_name or ''}\n"
                )
    await message.answer(text)

@router.message(F.text == "Бонусная система")
async def btn_bonus_system(message: Message, state: FSMContext):
    async with async_session() as session:
        # Total bonus amount earned/spent
        result = await session.execute(
            select(func.sum(BonusTransaction.amount))
        )
        total_bonus = result.scalar_one() or 0
        # Count of transactions
        cnt_result = await session.execute(
            select(func.count()).select_from(BonusTransaction)
        )
        cnt = cnt_result.scalar_one()
        text = (
            f"Бонусная система:\n"
            f"Всего начислено бонусов: {total_bonus} баллов\n"
            f"Количество транзакций: {cnt}\n"
        )
    await message.answer(text)

@router.message(F.text == "Наша команда")
async def btn_our_team(message: Message, state: FSMContext):
    await message.answer(
        "Наша команда звукорежиссеров:\n"
        "• Иванов Иван (ведущий инженер)\n"
        "• Петр Петров (запись и микс)\n"
        "• Сидорова Анна (мастеринг)\n"
        "Вы можете выбрать любого из них при записи.",
        reply_markup=get_main_admin_keyboard()
    )

@router.message(F.text == "Настройки")
async def btn_settings(message: Message, state: FSMContext):
    await message.answer(
        "Настройки пока не реализованы.\n"
        "Скоро здесь будут возможности изменить рабочее время, стоимость часа и т.д.",
        reply_markup=get_main_admin_keyboard()
    )