from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from src.bot.states import AdminStates
from src.bot.keyboards.common import get_main_admin_keyboard, get_cancel_keyboard
from src.bot.keyboards.admin import (
    get_clients_keyboard,
    get_client_details_keyboard,
    get_add_user_keyboard
)
from src.bot.database import async_session
from src.models.user import User
from src.models.studio_settings import StudioSettings
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
    telegram_id_str = (message.text or "").strip()
    if not telegram_id_str.isdigit():
        await message.answer("Telegram ID должен быть числом без пробелов и других символов. Попробуйте снова.")
        return
    telegram_id = int(telegram_id_str)
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
            added = True
        else:
            user.role = "engineer"
            user.is_active = True
            user.is_admin = False
            added = False
        await session.commit()
        await session.refresh(user)
    await state.clear()
    if added:
        await message.answer(
            f"Пользователь с Telegram ID {telegram_id} теперь является звукорежиссером.",
            reply_markup=get_main_admin_keyboard()
        )
    else:
        await message.answer(
            f"Пользователь с Telegram ID {telegram_id} уже существовал и теперь назначен звукорежиссером.",
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
    telegram_id_str = (message.text or "").strip()
    if not telegram_id_str.isdigit():
        await message.answer("Telegram ID должен быть числом без пробелов и других символов. Попробуйте снова.")
        return
    telegram_id = int(telegram_id_str)
    async with async_session() as session:
        # Check if user exists
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
            added = True
        else:
            user.role = "admin"
            user.is_active = True
            user.is_admin = True
            added = False
        await session.commit()
        await session.refresh(user)
    await state.clear()
    if added:
        await message.answer(
            f"Пользователь с Telegram ID {telegram_id} теперь является администратором.",
            reply_markup=get_main_admin_keyboard()
        )
    else:
        await message.answer(
            f"Пользователь с Telegram ID {telegram_id} уже существовал и теперь назначен администратором.",
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
        pending = await session.execute(
            select(Booking).where(Booking.status == BookingStatus.PENDING)
        )
        pending_cnt = len(pending.scalars().all())
        text = f"Количество новых заявок (Pending): {pending_cnt}"
    # Send new message to avoid any edit issues
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "stat_confirmed")
async def process_stat_confirmed(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        confirmed = await session.execute(
            select(Booking).where(Booking.status == BookingStatus.CONFIRMED)
        )
        confirmed_cnt = len(confirmed.scalars().all())
        text = f"Подтвержденные записи: {confirmed_cnt}"
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "stat_cancellations")
async def process_stat_cancellations(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        cancelled = await session.execute(
            select(Booking).where(Booking.status.in_([BookingStatus.CANCELLED_CLIENT, BookingStatus.CANCELLED_ENGINEER]))
        )
        cancelled_cnt = len(cancelled.scalars().all())
        text = f"Отмены: {cancelled_cnt}"
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "stat_revenue")
async def process_stat_revenue(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(
            select(func.sum(Booking.total_price)).where(Booking.status == BookingStatus.COMPLETED)
        )
        total = result.scalar_one() or 0
        text = f"Выручка (завершенные записи): {total} руб."
    await callback.message.answer(text)
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
            await message.answer("Звукорежиссеров нет.")
            return
        # Build inline keyboard with engineers and edit buttons
        builder = InlineKeyboardBuilder()
        for eng in engineers:
            # Button with engineer name
            builder.button(
                text=f"{eng.first_name or ''} {eng.last_name or ''}".strip(),
                callback_data=f"engineer_view:{eng.id}"
            )
            # Button to edit engineer
            builder.button(
                text="Изменить",
                callback_data=f"engineer_edit:{eng.id}"
            )
        builder.button(text="🔙 Назад", callback_data="back_to_admin_main")
        builder.adjust(2)  # Two buttons per row: name and edit
        await message.answer(
            "Выберите звукорежиссера для просмотра или редактирования:",
            reply_markup=builder.as_markup()
        )

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
        "• Иванов Иван (ведущий ingeniero)\n"
        "• Петр Петров (запись и микс)\n"
        "• Сидорова Анна (мастеринг)\n"
        "Вы можете выбрать любого из них при записи.",
        reply_markup=get_main_admin_keyboard()
    )

@router.message(F.text == "Настройки")
async def btn_settings(message: Message, state: FSMContext):
    # Get studio settings (singleton)
    async with async_session() as session:
        result = await session.execute(select(StudioSettings).limit(1))
        settings = result.scalar_one_or_none()
        if not settings:
            # Create default settings if none exist
            settings = StudioSettings()
            session.add(settings)
            await session.commit()
            await session.refresh(settings)
    text = (
        f"Текущие настройки студии:\n"
        f"📞 Телефон: {settings.phone or 'не указан'}\n"
        f"📧 Email: {settings.email or 'не указан'}\n"
        f"📍 Адрес: {settings.address or 'не указан'}\n"
        f"🕒 Рабочее время: {settings.work_hours_start.strftime('%H:%M') if settings.work_hours_start else 'не указано'} – "
        f"{settings.work_hours_end.strftime('%H:%M') if settings.work_hours_end else 'не указано'}\n"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить телефон", callback_data="settings_edit_phone")
    builder.button(text="Изменить email", callback_data="settings_edit_email")
    builder.button(text="Изменить адрес", callback_data="settings_edit_address")
    builder.button(text="Изменить рабочее время", callback_data="settings_edit_work_hours")
    builder.button(text="🔙 Назад", callback_data="back_to_admin_main")
    builder.adjust(1)
    await message.answer(
        text,
        reply_markup=builder.as_markup()
    )

# Engineer detail viewing and editing
@router.callback_query(F.data.startswith("engineer_view:"))
async def cb_engineer_view(callback: CallbackQuery, state: FSMContext):
    engineer_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        engineer = await session.get(User, engineer_id)
        if not engineer:
            await callback.answer("Инженер не найден.", show_alert=True)
            return
        # Get some stats
        bookings_count = await session.execute(
            select(func.count()).select_from(Booking).where(Booking.engineer_id == engineer_id)
        )
        completed_count = await session.execute(
            select(func.count()).select_from(Booking).where(
                Booking.engineer_id == engineer_id,
                Booking.status == BookingStatus.COMPLETED
            )
        )
        cancelled_count = await session.execute(
            select(func.count()).select_from(Booking).where(
                Booking.engineer_id == engineer_id,
                Booking.status.in_([BookingStatus.CANCELLED_CLIENT, BookingStatus.CANCELLED_ENGINEER])
            )
        )
        total_earnings = await session.execute(
            select(func.sum(Booking.total_price)).where(
                Booking.engineer_id == engineer_id,
                Booking.status == BookingStatus.COMPLETED
            )
        )
    text = (
        f"Инженер: {engineer.first_name} {engineer.last_name or ''}\n"
        f"Username: @{engineer.username or 'не указан'}\n"
        f"Телефон: {engineer.phone_number or 'не указан'}\n"
        f"Ставка: {engineer.hourly_rate or 'не указана'} руб/ч\n"
        f"Описание: {engineer.description or 'не указано'}\n"
        f"Фото: {'есть' if engineer.photo_file_id else 'отсутствует'}\n"
        f"\nСтатистика:\n"
        f"Всего записей: {bookings_count.scalar()}\n"
        f"Завершенных: {completed_count.scalar()}\n"
        f"Отменено: {cancelled_count.scalar()}\n"
        f"Заработано: {total_earnings.scalar() or 0} руб.\n"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить ставку", callback_data=f"engineer_edit_rate:{engineer_id}")
    builder.button(text="Изменить описание", callback_data=f"engineer_edit_desc:{engineer_id}")
    builder.button(text="Изменить фото", callback_data=f"engineer_edit_photo:{engineer_id}")
    builder.button(text="🔙 Назад к списку", callback_data="engineers_list")
    builder.adjust(1)
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "engineers_list")
async def cb_engineers_list(callback: CallbackQuery, state: FSMContext):
    # Go back to the engineer list
    await btn_engineers(callback.message, state)
    await callback.answer()

# Engineer editing handlers
@router.callback_query(F.data.startswith("engineer_edit_rate:"))
async def cb_engineer_edit_rate(callback: CallbackQuery, state: FSMContext):
    engineer_id = int(callback.data.split(":")[1])
    await state.update_data(engineer_id=engineer_id)
    await state.set_state(AdminStates.editing_engineer_hourly_rate)
    await callback.message.edit_text(
        "Введите новую ставку за час (целое число):",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(AdminStates.editing_engineer_hourly_rate)
async def process_engineer_rate(message: Message, state: FSMContext):
    data = await state.get_data()
    engineer_id = data.get("engineer_id")
    rate_str = (message.text or "").strip()
    if not rate_str.isdigit():
        await message.answer("Ставка должна быть целым числом. Попробуйте снова.")
        return
    rate = int(rate_str)
    async with async_session() as session:
        engineer = await session.get(User, engineer_id)
        if not engineer:
            await message.answer("Инженер не найден.")
            await state.clear()
            return
        engineer.hourly_rate = rate
        await session.commit()
    await state.clear()
    await message.answer(
        f"Ставка инженера обновлена: {rate} руб/ч",
        reply_markup=get_main_admin_keyboard()
    )

@router.callback_query(F.data.startswith("engineer_edit_desc:"))
async def cb_engineer_edit_desc(callback: CallbackQuery, state: FSMContext):
    engineer_id = int(callback.data.split(":")[1])
    await state.update_data(engineer_id=engineer_id)
    await state.set_state(AdminStates.editing_engineer_description)
    await callback.message.edit_text(
        "Введите новое описание инженера:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(AdminStates.editing_engineer_description)
async def process_engineer_description(message: Message, state: FSMContext):
    data = await state.get_data()
    engineer_id = data.get("engineer_id")
    description = (message.text or "").strip()
    async with async_session() as session:
        engineer = await session.get(User, engineer_id)
        if not engineer:
            await message.answer("Инженер не найден.")
            await state.clear()
            return
        engineer.description = description
        await session.commit()
    await state.clear()
    await message.answer(
        f"Описание инженера обновлено.",
        reply_markup=get_main_admin_keyboard()
    )

@router.callback_query(F.data.startswith("engineer_edit_photo:"))
async def cb_engineer_edit_photo(callback: CallbackQuery, state: FSMContext):
    engineer_id = int(callback.data.split(":")[1])
    await state.update_data(engineer_id=engineer_id)
    await state.set_state(AdminStates.editing_engineer_photo)
    await callback.message.edit_text(
        "Отправьте новое фото инженера (как фото):",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(AdminStates.editing_engineer_photo, F.photo)
async def process_engineer_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    engineer_id = data.get("engineer_id")
    # Get the largest photo
    photo = message.photo[-1]
    file_id = photo.file_id
    async with async_session() as session:
        engineer = await session.get(User, engineer_id)
        if not engineer:
            await message.answer("Инженер не найден.")
            await state.clear()
            return
        engineer.photo_file_id = file_id
        await session.commit()
    await state.clear()
    await message.answer(
        f"Фото инженера обновлено.",
        reply_markup=get_main_admin_keyboard()
    )

# Cancel any editing
@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.")
        return
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_admin_keyboard()
    )

# Settings editing handlers (from previous version)
@router.callback_query(F.data == "settings_edit_phone")
async def cb_settings_edit_phone(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.editing_studio_phone)
    await callback.message.edit_text(
        "Введите новый телефон студии:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(AdminStates.editing_studio_phone)
async def process_settings_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    async with async_session() as session:
        result = await session.execute(select(StudioSettings).limit(1))
        settings = result.scalar_one_or_none()
        if not settings:
            settings = StudioSettings()
            session.add(settings)
        settings.phone = phone
        await session.commit()
    await state.clear()
    await message.answer(
        f"Телефон студии обновлен: {phone}",
        reply_markup=get_main_admin_keyboard()
    )

@router.callback_query(F.data == "settings_edit_email")
async def cb_settings_edit_email(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.editing_studio_email)
    await callback.message.edit_text(
        "Введите новый email студии:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(AdminStates.editing_studio_email)
async def process_settings_email(message: Message, state: FSMContext):
    email = (message.text or "").strip()
    async with async_session() as session:
        result = await session.execute(select(StudioSettings).limit(1))
        settings = result.scalar_one_or_none()
        if not settings:
            settings = StudioSettings()
            session.add(settings)
        settings.email = email
        await session.commit()
    await state.clear()
    await message.answer(
        f"Email студии обновлен: {email}",
        reply_markup=get_main_admin_keyboard()
    )

@router.callback_query(F.data == "settings_edit_address")
async def cb_settings_edit_address(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.editing_studio_address)
    await callback.message.edit_text(
        "Введите новый адрес студии:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(AdminStates.editing_studio_address)
async def process_settings_address(message: Message, state: FSMContext):
    address = (message.text or "").strip()
    async with async_session() as session:
        result = await session.execute(select(StudioSettings).limit(1))
        settings = result.scalar_one_or_none()
        if not settings:
            settings = StudioSettings()
            session.add(settings)
        settings.address = address
        await session.commit()
    await state.clear()
    await message.answer(
        f"Адрес студии обновлен: {address}",
        reply_markup=get_main_admin_keyboard()
    )

@router.callback_query(F.data == "settings_edit_work_hours")
async def cb_settings_edit_work_hours(callback: CallbackQuery, state: FSMContext):
    # Placeholder
    await callback.message.edit_text(
        "Редактирование рабочего времени пока не реализовано. Используйте файл настроек или обратитесь к разработчику.",
        reply_markup=get_main_admin_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_admin_main")
async def cb_back_to_admin_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Вы вернулись в главное меню админ-панели",
        reply_markup=None
    )
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_admin_keyboard()
    )
    await callback.answer()