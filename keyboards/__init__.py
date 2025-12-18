"""
Клавиатуры для бота.
"""
from .inline import get_subscribe_keyboard, get_event_keyboard, get_events_list_keyboard
from .reply import get_main_keyboard

__all__ = [
    "get_subscribe_keyboard",
    "get_event_keyboard",
    "get_events_list_keyboard",
    "get_main_keyboard"
]

