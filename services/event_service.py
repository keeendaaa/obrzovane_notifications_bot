"""
Сервис для работы с мероприятиями.
Содержит бизнес-логику, связанную с мероприятиями.
"""
from datetime import datetime
from typing import Optional, List
from models.event import Event
import pytz
from config import Config


class EventService:
    """
    Сервис для работы с мероприятиями.
    Содержит методы для валидации и обработки данных мероприятий.
    """
    
    @staticmethod
    def parse_datetime(date_string: str) -> Optional[datetime]:
        """
        Парсит строку с датой и временем в объект datetime.
        
        Args:
            date_string: Строка с датой в формате ДД.ММ.ГГГГ ЧЧ:ММ
            
        Returns:
            Объект datetime или None при ошибке
        """
        try:
            dt = datetime.strptime(date_string, "%d.%m.%Y %H:%M")
            timezone = pytz.timezone(Config.TIMEZONE)
            return timezone.localize(dt)
        except ValueError:
            return None
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """
        Форматирует datetime в строку для отображения.
        
        Args:
            dt: Объект datetime
            
        Returns:
            Отформатированная строка
        """
        return dt.strftime("%d.%m.%Y в %H:%M")
    
    @staticmethod
    async def get_events_by_date_range(start_date: datetime, end_date: datetime) -> List[Event]:
        """
        Получает мероприятия в указанном диапазоне дат.
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            
        Returns:
            Список мероприятий
        """
        all_events = await Event.get_all()
        filtered_events = []
        
        for event in all_events:
            try:
                event_dt = datetime.fromisoformat(event.event_datetime)
                if start_date <= event_dt <= end_date:
                    filtered_events.append(event)
            except:
                continue
        
        return filtered_events
    
    @staticmethod
    def validate_event_data(
        title: str,
        event_datetime: str,
        format: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Валидирует данные мероприятия.
        
        Args:
            title: Название мероприятия
            event_datetime: Дата и время в ISO формате
            format: Формат мероприятия
            
        Returns:
            Кортеж (is_valid, error_message)
        """
        if not title or len(title.strip()) == 0:
            return False, "Название мероприятия не может быть пустым"
        
        try:
            dt = datetime.fromisoformat(event_datetime)
            if dt < datetime.now():
                return False, "Дата мероприятия не может быть в прошлом"
        except ValueError:
            return False, "Неверный формат даты и времени"
        
        if format and format not in ["online", "offline", "hybrid"]:
            return False, "Формат должен быть: online, offline или hybrid"
        
        return True, None

