from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def get_clients_keyboard(clients):
    builder = InlineKeyboardBuilder()
    for client in clients:
        builder.button(
            text=f"{client.first_name} {client.last_name or ''} (@{client.username or 'нет_username'})",
            callback_data=f"client:{client.id}"
        )
    builder.adjust(1)
    return builder.as_markup()

def get_client_details_keyboard(client_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="История записей", callback_data=f"client_history:{client_id}")
    builder.button(text="История бонусов", callback_data=f"client_bonuses:{client_id}")
    builder.button(text="История рефералов", callback_data=f"client_referrals:{client_id}")
    builder.button(text="🔙 Назад к списку", callback_data="back_to_clients")
    builder.adjust(1)
    return builder.as_markup()

def get_add_user_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Да", callback_data="add_user_yes")
    builder.button(text="Нет", callback_data="add_user_no")
    builder.adjust(2)
    return builder.as_markup()

# Placeholder for other admin keyboards
def get_statistics_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Заявки", callback_data="stat_requests")
    builder.button(text="Подтвержденные записи", callback_data="stat_confirmed")
    builder.button(text="Отмены", callback_data="stat_cancellations")
    builder.button(text="Выручка", callback_data="stat_revenue")
    builder.adjust(2)
    return builder.as_markup()