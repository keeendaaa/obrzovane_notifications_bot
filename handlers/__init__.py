"""
Обработчики команд и сообщений бота.
"""
from .start import register_start_handlers
from .admin import register_admin_handlers
from .notifications import register_notification_handlers

__all__ = [
    "register_start_handlers",
    "register_admin_handlers",
    "register_notification_handlers"
]

