from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, KeyboardButton

def get_confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm")
    builder.button(text="✏️ Изменить", callback_data="edit")
    builder.button(text="❌ Отменить", callback_data="cancel")
    builder.adjust(3)
    return builder.as_markup()

def get_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back")
    return builder.as_markup()

def get_main_client_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Записаться")
    builder.button(text="Ночная запись")
    builder.button(text="Наша команда")
    builder.button(text="Мои записи")
    builder.button(text="Бонусы и рефералы")
    builder.button(text="Контакты студии")
    builder.button(text="Помощь")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_main_engineer_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Новые заявки")
    builder.button(text="Ночные заявки")
    builder.button(text="Мои записи")
    builder.button(text="Расписание")
    builder.button(text="График работы")
    builder.button(text="Связаться с клиентом")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_main_admin_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Статистика")
    builder.button(text="Все записи")
    builder.button(text="Ночные записи")
    builder.button(text="Клиенты")
    builder.button(text="Пользователи")
    builder.button(text="Звукорежиссеры")
    builder.button(text="Администраторы")
    builder.button(text="Бонусная система")
    builder.button(text="Наша команда")
    builder.button(text="Настройки")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)