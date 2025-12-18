"""
Конфигурация бота.
Загружает настройки из переменных окружения.
"""
import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    """Класс для хранения конфигурации бота"""
    
    # Токен бота из переменной окружения
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # ID администраторов (список через запятую в .env)
    ADMIN_IDS: List[int] = [
        int(admin_id.strip())
        for admin_id in os.getenv("ADMIN_IDS", "").split(",")
        if admin_id.strip().isdigit()
    ]
    
    # Часовой пояс для работы с датами
    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")
    
    # Время уведомлений до начала мероприятия (в часах)
    # Например: "24,1" означает уведомления за 24 часа и за 1 час
    NOTIFICATION_HOURS: List[int] = [
        int(hour.strip())
        for hour in os.getenv("NOTIFICATION_HOURS", "24,1").split(",")
        if hour.strip().isdigit()
    ]
    
    # Путь к базе данных
    DATABASE_PATH: str = "bot_database.db"
    
    @classmethod
    def validate(cls) -> bool:
        """
        Проверяет, что все необходимые настройки заполнены.
        Возвращает True, если конфигурация валидна.
        """
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        if not cls.ADMIN_IDS:
            raise ValueError("ADMIN_IDS не установлен в .env файле")
        return True

