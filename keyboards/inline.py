"""
Inline-клавиатуры для бота.
Используются для интерактивных кнопок под сообщениями.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


def get_subscribe_keyboard(is_subscribed: bool) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для подписки/отписки.
    
    Args:
        is_subscribed: Текущий статус подписки пользователя
        
    Returns:
        InlineKeyboardMarkup с кнопками подписки
    """
    if is_subscribed:
        button = InlineKeyboardButton(
            text="❌ Отписаться от уведомлений",
            callback_data="unsubscribe"
        )
    else:
        button = InlineKeyboardButton(
            text="✅ Подписаться на уведомления",
            callback_data="subscribe"
        )
    
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


def get_event_keyboard(event_id: int, show_delete: bool = False) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для управления мероприятием (для админов).
    
    Args:
        event_id: ID мероприятия
        show_delete: Показывать ли кнопку удаления
        
    Returns:
        InlineKeyboardMarkup с кнопками управления
    """
    buttons = []
    
    if show_delete:
        buttons.append([
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"delete_event_{event_id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"edit_event_{event_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_events_list_keyboard(events: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком мероприятий (пагинация).
    
    Args:
        events: Список мероприятий
        page: Номер страницы (начинается с 0)
        per_page: Количество мероприятий на странице
        
    Returns:
        InlineKeyboardMarkup со списком мероприятий
    """
    buttons = []
    start_idx = page * per_page
    end_idx = start_idx + per_page
    
    for event in events[start_idx:end_idx]:
        buttons.append([
            InlineKeyboardButton(
                text=f"📅 {event.title[:30]}...",
                callback_data=f"view_event_{event.id}"
            )
        ])
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"events_page_{page - 1}")
        )
    if end_idx < len(events):
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ▶️", callback_data=f"events_page_{page + 1}")
        )
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру подтверждения действия.
    
    Args:
        action: Тип действия (например, "delete")
        item_id: ID элемента
        
    Returns:
        InlineKeyboardMarkup с кнопками подтверждения
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да",
                callback_data=f"confirm_{action}_{item_id}"
            ),
            InlineKeyboardButton(
                text="❌ Нет",
                callback_data=f"cancel_{action}_{item_id}"
            )
        ]
    ])

