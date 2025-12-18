"""
Инициализация и управление базой данных.
Использует aiosqlite для асинхронной работы с SQLite.
"""
import aiosqlite
from typing import Optional
from config import Config


class Database:
    """
    Класс для работы с базой данных.
    Использует паттерн Singleton для единой точки доступа.
    """
    _instance: Optional['Database'] = None
    _connection: Optional[aiosqlite.Connection] = None
    
    def __new__(cls):
        """Реализация паттерна Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Устанавливает соединение с базой данных"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(Config.DATABASE_PATH)
            # Включаем поддержку внешних ключей
            await self._connection.execute("PRAGMA foreign_keys = ON")
            await self._connection.commit()
    
    async def close(self):
        """Закрывает соединение с базой данных"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def execute(self, query: str, params: tuple = ()):
        """
        Выполняет SQL запрос (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
        """
        if self._connection is None:
            await self.connect()
        await self._connection.execute(query, params)
        await self._connection.commit()
    
    async def fetch_one(self, query: str, params: tuple = ()):
        """
        Выполняет SQL запрос и возвращает одну строку.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            Результат запроса или None
        """
        if self._connection is None:
            await self.connect()
        async with self._connection.execute(query, params) as cursor:
            return await cursor.fetchone()
    
    async def fetch_all(self, query: str, params: tuple = ()):
        """
        Выполняет SQL запрос и возвращает все строки.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            Список результатов запроса
        """
        if self._connection is None:
            await self.connect()
        async with self._connection.execute(query, params) as cursor:
            return await cursor.fetchall()
    
    async def init_db(self):
        """
        Инициализирует базу данных: создает таблицы, если их нет.
        Вызывается при первом запуске бота.
        """
        if self._connection is None:
            await self.connect()
        
        # Таблица пользователей
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                is_subscribed INTEGER NOT NULL DEFAULT 1,
                registered_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        
        # Таблица мероприятий
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                event_datetime TEXT NOT NULL,
                location TEXT,
                format TEXT CHECK(format IN ('online', 'offline', 'hybrid')),
                link TEXT,
                photo_file_id TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        
        # Добавляем колонку photo_file_id, если её нет (для существующих БД)
        try:
            await self._connection.execute("ALTER TABLE events ADD COLUMN photo_file_id TEXT")
            await self._connection.commit()
        except Exception:
            # Колонка уже существует, игнорируем ошибку
            pass
        
        # Таблица для отслеживания отправленных уведомлений
        # Предотвращает дублирование напоминаний
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS sent_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                hours_before INTEGER NOT NULL,
                sent_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                UNIQUE(event_id, hours_before)
            )
        """)
        
        await self._connection.commit()


# Глобальный экземпляр базы данных
db = Database()

