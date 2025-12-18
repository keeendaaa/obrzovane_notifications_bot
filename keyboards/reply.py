"""
Reply-клавиатуры для бота.
Используются для постоянных кнопок внизу экрана.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает главную клавиатуру для пользователей.
    
    Returns:
        ReplyKeyboardMarkup с основными командами
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Предстоящие мероприятия")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для администраторов.
    
    Returns:
        ReplyKeyboardMarkup с админ-командами
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/add_event"),
                KeyboardButton(text="/list_events")
            ],
            [
                KeyboardButton(text="/edit_event"),
                KeyboardButton(text="/delete_event")
            ],
            [
                KeyboardButton(text="/send_test_notification"),
                KeyboardButton(text="/stats")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard

