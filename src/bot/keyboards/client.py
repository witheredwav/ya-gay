from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from datetime import datetime, timedelta
import calendar

def get_month_keyboard():
    builder = InlineKeyboardBuilder()
    now = datetime.now()
    for i in range(12):
        month = (now.month - 1 + i) % 12 + 1
        year = now.year + ((now.month - 1 + i) // 12)
        builder.button(
            text=datetime(year, month, 1).strftime("%B %Y"),
            callback_data=f"month:{month}"
        )
    builder.adjust(3)
    return builder.as_markup()

def get_date_keyboard(month: int):
    builder = InlineKeyboardBuilder()
    now = datetime.now()
    year = now.year
    if month < now.month:
        year = now.year + 1
    elif month == now.month and now.day > 25:  # Simplified: if late in month, show next month
        year = now.year + 1
    _, num_days = calendar.monthrange(year, month)
    for day in range(1, num_days + 1):
        builder.button(
            text=str(day),
            callback_data=f"date:{day}"
        )
    builder.adjust(7)
    return builder.as_markup()

def get_engineer_keyboard():
    builder = InlineKeyboardBuilder()
    # In reality, fetch from DB
    builder.button(text="Инженер 1", callback_data="engineer:1")
    builder.button(text="Инженер 2", callback_data="engineer:2")
    builder.adjust(2)
    return builder.as_markup()

def get_time_keyboard():
    builder = InlineKeyboardBuilder()
    times = ["11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00"]
    for time in times:
        builder.button(text=time, callback_data=f"time:{time}")
    builder.adjust(4)
    return builder.as_markup()

def get_duration_keyboard():
    builder = InlineKeyboardBuilder()
    durations = [1, 2, 3, 4, 5, 6]
    for dur in durations:
        builder.button(text=f"{dur} час(а)", callback_data=f"duration:{dur}")
    builder.adjust(3)
    return builder.as_markup()