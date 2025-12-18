"""
Модель мероприятия.
Представляет мероприятие в базе данных.
"""
from datetime import datetime
from typing import Optional
from database import db


class Event:
    """
    Модель мероприятия.
    
    Атрибуты:
        id: Уникальный идентификатор мероприятия
        title: Название мероприятия
        description: Описание мероприятия
        event_datetime: Дата и время проведения (ISO формат)
        location: Место проведения
        format: Формат (online/offline/hybrid)
        link: Ссылка на мероприятие
        photo_file_id: ID файла фото в Telegram (если есть)
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """
    
    def __init__(
        self,
        title: str,
        event_datetime: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        format: Optional[str] = None,
        link: Optional[str] = None,
        photo_file_id: Optional[str] = None,
        event_id: Optional[int] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.id = event_id
        self.title = title
        self.description = description or ""
        self.event_datetime = event_datetime
        self.location = location or ""
        self.format = format or "offline"
        self.link = link or ""
        self.photo_file_id = photo_file_id or ""
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
    
    async def save(self) -> int:
        """
        Сохраняет мероприятие в БД.
        Если id не установлен, создает новую запись.
        Если id установлен, обновляет существующую.
        
        Returns:
            ID сохраненного мероприятия
        """
        if self.id is None:
            # Создаем новое мероприятие
            cursor = await db._connection.execute(
                """
                INSERT INTO events (title, description, event_datetime, location, format, link, photo_file_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (self.title, self.description, self.event_datetime, self.location, self.format, self.link, self.photo_file_id)
            )
            await db._connection.commit()
            self.id = cursor.lastrowid
        else:
            # Обновляем существующее мероприятие
            self.updated_at = datetime.now().isoformat()
            await db.execute(
                """
                UPDATE events 
                SET title = ?, description = ?, event_datetime = ?, 
                    location = ?, format = ?, link = ?, photo_file_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (self.title, self.description, self.event_datetime, self.location, 
                 self.format, self.link, self.photo_file_id, self.updated_at, self.id)
            )
        return self.id
    
    async def delete(self):
        """Удаляет мероприятие из БД"""
        if self.id is not None:
            await db.execute("DELETE FROM events WHERE id = ?", (self.id,))
    
    @classmethod
    async def get_by_id(cls, event_id: int) -> Optional['Event']:
        """
        Получает мероприятие по ID.
        
        Args:
            event_id: ID мероприятия
            
        Returns:
            Объект Event или None, если не найдено
        """
        row = await db.fetch_one(
            "SELECT id, title, description, event_datetime, location, format, link, photo_file_id, created_at, updated_at FROM events WHERE id = ?",
            (event_id,)
        )
        
        if row:
            return cls(
                event_id=row[0],
                title=row[1],
                description=row[2],
                event_datetime=row[3],
                location=row[4],
                format=row[5],
                link=row[6],
                photo_file_id=row[7] if len(row) > 7 else None,
                created_at=row[8] if len(row) > 8 else None,
                updated_at=row[9] if len(row) > 9 else None
            )
        return None
    
    @staticmethod
    async def get_all() -> list['Event']:
        """
        Получает все мероприятия из БД.
        
        Returns:
            Список всех мероприятий
        """
        rows = await db.fetch_all(
            "SELECT id, title, description, event_datetime, location, format, link, photo_file_id, created_at, updated_at FROM events ORDER BY event_datetime ASC"
        )
        
        events = []
        for row in rows:
            events.append(Event(
                event_id=row[0],
                title=row[1],
                description=row[2],
                event_datetime=row[3],
                location=row[4],
                format=row[5],
                link=row[6],
                photo_file_id=row[7] if len(row) > 7 else None,
                created_at=row[8] if len(row) > 8 else None,
                updated_at=row[9] if len(row) > 9 else None
            ))
        return events
    
    @staticmethod
    async def get_upcoming() -> list['Event']:
        """
        Получает предстоящие мероприятия (дата >= текущей).
        
        Returns:
            Список предстоящих мероприятий
        """
        current_time = datetime.now().isoformat()
        rows = await db.fetch_all(
            "SELECT id, title, description, event_datetime, location, format, link, photo_file_id, created_at, updated_at FROM events WHERE event_datetime >= ? ORDER BY event_datetime ASC",
            (current_time,)
        )
        
        events = []
        for row in rows:
            events.append(Event(
                event_id=row[0],
                title=row[1],
                description=row[2],
                event_datetime=row[3],
                location=row[4],
                format=row[5],
                link=row[6],
                photo_file_id=row[7] if len(row) > 7 else None,
                created_at=row[8] if len(row) > 8 else None,
                updated_at=row[9] if len(row) > 9 else None
            ))
        return events
    
    def format_message(self) -> str:
        """
        Форматирует мероприятие в читаемое сообщение для пользователя.
        
        Returns:
            Отформатированное сообщение
        """
        try:
            event_dt = datetime.fromisoformat(self.event_datetime)
            formatted_date = event_dt.strftime("%d.%m.%Y в %H:%M")
        except:
            formatted_date = self.event_datetime
        
        message = f"🎯 <b>{self.title}</b>\n\n"
        
        if self.description:
            message += f"{self.description}\n\n"
        
        message += f"📅 <b>Дата и время:</b> {formatted_date}\n"
        
        if self.location:
            message += f"📍 <b>Место:</b> {self.location}\n"
        
        if self.format:
            format_emoji = {
                "online": "💻",
                "offline": "🏢",
                "hybrid": "🔀"
            }
            format_text = {
                "online": "Онлайн",
                "offline": "Офлайн",
                "hybrid": "Гибрид"
            }
            emoji = format_emoji.get(self.format, "📌")
            text = format_text.get(self.format, self.format)
            message += f"{emoji} <b>Формат:</b> {text}\n"
        
        if self.link:
            message += f"\n🔗 <a href='{self.link}'>Ссылка на мероприятие</a>"
        
        return message

