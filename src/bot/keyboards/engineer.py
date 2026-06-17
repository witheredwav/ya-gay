from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def get_new_requests_keyboard(bookings):
    builder = InlineKeyboardBuilder()
    for booking in bookings:
        builder.button(
            text=f"Заявка #{booking.id} от {booking.start_time.strftime('%d.%m %H:%M')}",
            callback_data=f"request:{booking.id}"
        )
    builder.adjust(1)
    return builder.as_markup()

def get_request_details_keyboard(booking_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data=f"confirm_request:{booking_id}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_request:{booking_id}")
    builder.button(text="🔙 Назад к списку", callback_data="back_to_requests")
    builder.adjust(2)
    return builder.as_markup()

# Placeholder for other engineer keyboards (schedule, etc.)
def get_schedule_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Установить график работы", callback_data="set_schedule")
    builder.button(text="Добавить выходной", callback_data="add_day_off")
    builder.button(text="Посмотреть текущий график", callback_data="view_schedule")
    builder.adjust(1)
    return builder.as_markup()