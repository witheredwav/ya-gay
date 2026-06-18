from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from datetime import datetime, timedelta
import calendar

# Russian month names
month_names = [
    "", "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
]

def get_month_keyboard():
    builder = InlineKeyboardBuilder()
    now = datetime.now()
    # Current month
    month = now.month
    year = now.year
    builder.button(
        text=f"{month_names[month].capitalize()} {year}",
        callback_data=f"month:{month}"
    )
    # Next month
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    builder.button(
        text=f"{month_names[month].capitalize()} {year}",
        callback_data=f"month:{month}"
    )
    builder.button(text="🔙 Назад", callback_data="back_to_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_date_keyboard(month: int):
    builder = InlineKeyboardBuilder()
    now = datetime.now()
    year = now.year
    if month < now.month:
        year = now.year + 1
    elif month == now.month and now.day > 25:  # If late in month, show next month
        year = now.year + 1
    _, num_days = calendar.monthrange(year, month)
    # Determine start day: if current month, start from today; else from 1
    if month == now.month and year == now.year:
        start_day = now.day
    else:
        start_day = 1
    for day in range(start_day, num_days + 1):
        builder.button(
            text=str(day),
            callback_data=f"date:{day}"
        )
    builder.button(text="🔙 Назад", callback_data="back_to_month")
    builder.adjust(7, 1)
    return builder.as_markup()

def get_engineer_keyboard():
    builder = InlineKeyboardBuilder()
    # In reality, fetch from DB
    builder.button(text="Инженер 1", callback_data="engineer:1")
    builder.button(text="Инженер 2", callback_data="engineer:2")
    builder.button(text="🔙 Назад", callback_data="back_to_date")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_time_keyboard():
    builder = InlineKeyboardBuilder()
    now = datetime.now()
    # Work hours: 11:00 to 22:00, slot step 30 minutes
    # Round up current time to next half hour
    if now.minute < 30:
        rounded = now.replace(minute=30, second=0, microsecond=0)
    else:
        rounded = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    # If rounded time is after workday end, no slots
    work_start = now.replace(hour=11, minute=0, second=0, microsecond=0)
    work_end = now.replace(hour=22, minute=0, second=0, microsecond=0)
    if rounded > work_end:
        # No available slots today
        builder.button(text="Нет свободных слотов", callback_data="none")
    else:
        # Generate time slots from max(work_start, rounded) to work_end step 30 min
        current = max(work_start, rounded)
        while current <= work_end:
            builder.button(
                text=current.strftime("%H:%M"),
                callback_data=f"time:{current.strftime('%H:%M')}"
            )
            current += timedelta(minutes=30)
    builder.button(text="🔙 Назад", callback_data="back_to_engineer")
    builder.adjust(4, 1)
    return builder.as_markup()

def get_duration_keyboard():
    builder = InlineKeyboardBuilder()
    durations = [1, 2, 3, 4, 5, 6]
    for dur in durations:
        builder.button(text=f"{dur} час(а)", callback_data=f"duration:{dur}")
    builder.button(text="🔙 Назад", callback_data="back_to_time")
    builder.adjust(3, 1)
    return builder.as_markup()