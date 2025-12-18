"""
Модель пользователя.
Представляет пользователя Telegram в базе данных.
"""
from datetime import datetime
from typing import Optional
from database import db


class User:
    """
    Модель пользователя.
    
    Атрибуты:
        telegram_id: ID пользователя в Telegram
        is_subscribed: Статус подписки (True/False)
        registered_at: Дата регистрации
    """
    
    def __init__(
        self,
        telegram_id: int,
        is_subscribed: bool = True,
        registered_at: Optional[str] = None
    ):
        self.telegram_id = telegram_id
        self.is_subscribed = is_subscribed
        self.registered_at = registered_at or datetime.now().isoformat()
    
    @classmethod
    async def get_or_create(cls, telegram_id: int) -> 'User':
        """
        Получает пользователя из БД или создает нового.
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Объект User
        """
        user_data = await db.fetch_one(
            "SELECT telegram_id, is_subscribed, registered_at FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        
        if user_data:
            return cls(
                telegram_id=user_data[0],
                is_subscribed=bool(user_data[1]),
                registered_at=user_data[2]
            )
        else:
            # Создаем нового пользователя
            await db.execute(
                "INSERT INTO users (telegram_id, is_subscribed) VALUES (?, ?)",
                (telegram_id, 1)
            )
            return cls(telegram_id=telegram_id)
    
    async def save(self):
        """Сохраняет изменения пользователя в БД"""
        await db.execute(
            """
            INSERT OR REPLACE INTO users (telegram_id, is_subscribed, registered_at)
            VALUES (?, ?, ?)
            """,
            (self.telegram_id, 1 if self.is_subscribed else 0, self.registered_at)
        )
    
    async def subscribe(self):
        """Подписывает пользователя на уведомления"""
        self.is_subscribed = True
        await self.save()
    
    async def unsubscribe(self):
        """Отписывает пользователя от уведомлений"""
        self.is_subscribed = False
        await self.save()
    
    @staticmethod
    async def get_subscribed_users() -> list[int]:
        """
        Получает список ID всех подписанных пользователей.
        
        Returns:
            Список telegram_id подписанных пользователей
        """
        rows = await db.fetch_all(
            "SELECT telegram_id FROM users WHERE is_subscribed = 1"
        )
        return [row[0] for row in rows]
    
    @staticmethod
    async def get_all_users_count() -> int:
        """
        Возвращает общее количество пользователей.
        
        Returns:
            Количество пользователей
        """
        row = await db.fetch_one("SELECT COUNT(*) FROM users")
        return row[0] if row else 0

