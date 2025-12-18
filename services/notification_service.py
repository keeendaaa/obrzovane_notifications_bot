"""
Сервис для отправки уведомлений пользователям.
Обрабатывает автоматическую рассылку при добавлении мероприятий
и напоминания о предстоящих событиях.
"""
from datetime import datetime, timedelta
from typing import List
from aiogram import Bot
from models.user import User
from models.event import Event
from config import Config
import pytz


class NotificationService:
    """
    Сервис для управления уведомлениями.
    Использует статические методы для удобства использования.
    """
    
    @staticmethod
    async def send_new_event_notification(event: Event, bot: Bot = None):
        """
        Отправляет уведомление о новом мероприятии всем подписанным пользователям.
        
        Args:
            event: Объект мероприятия
            bot: Экземпляр бота (если None, нужно передать через send_notification)
        """
        if bot is None:
            # Если бот не передан, уведомление будет отправлено через планировщик
            return
        
        subscribed_users = await User.get_subscribed_users()
        
        message_text = (
            "🎉 <b>Новое мероприятие!</b>\n\n"
            f"{event.format_message()}"
        )
        
        for user_id in subscribed_users:
            try:
                # Отправляем с фото, если оно есть
                if event.photo_file_id:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=event.photo_file_id,
                        caption=message_text,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
            except Exception as e:
                # Логируем ошибки, но не прерываем рассылку
                print(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
    
    @staticmethod
    async def send_upcoming_event_notification(event: Event, hours_before: int, bot: Bot):
        """
        Отправляет напоминание о предстоящем мероприятии.
        Проверяет, не было ли уже отправлено уведомление для этого мероприятия.
        
        Args:
            event: Объект мероприятия
            hours_before: За сколько часов до начала отправляется уведомление
            bot: Экземпляр бота
        """
        from database import db
        
        # Проверяем, не было ли уже отправлено это уведомление
        existing = await db.fetch_one(
            "SELECT id FROM sent_notifications WHERE event_id = ? AND hours_before = ?",
            (event.id, hours_before)
        )
        
        if existing:
            # Уведомление уже было отправлено
            return
        
        subscribed_users = await User.get_subscribed_users()
        
        hours_text = "час" if hours_before == 1 else "часа" if 2 <= hours_before <= 4 else "часов"
        
        message_text = (
            f"⏰ <b>Напоминание: через {hours_before} {hours_text}</b>\n\n"
            f"{event.format_message()}"
        )
        
        success_count = 0
        for user_id in subscribed_users:
            try:
                # Отправляем с фото, если оно есть
                if event.photo_file_id:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=event.photo_file_id,
                        caption=message_text,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                success_count += 1
            except Exception as e:
                print(f"Ошибка отправки напоминания пользователю {user_id}: {e}")
        
        # Сохраняем информацию об отправленном уведомлении
        if success_count > 0:
            await db.execute(
                "INSERT INTO sent_notifications (event_id, hours_before) VALUES (?, ?)",
                (event.id, hours_before)
            )
    
    @staticmethod
    async def check_and_send_reminders(bot: Bot):
        """
        Проверяет предстоящие мероприятия и отправляет напоминания,
        если до начала осталось нужное количество часов.
        
        Args:
            bot: Экземпляр бота
        """
        events = await Event.get_upcoming()
        timezone = pytz.timezone(Config.TIMEZONE)
        current_time = datetime.now(timezone)
        
        for event in events:
            try:
                # Парсим дату мероприятия
                event_datetime = datetime.fromisoformat(event.event_datetime)
                if event_datetime.tzinfo is None:
                    # Если часовой пояс не указан, используем конфигурированный
                    event_datetime = timezone.localize(event_datetime)
                else:
                    event_datetime = event_datetime.astimezone(timezone)
                
                # Проверяем каждое время уведомления из конфигурации
                for hours_before in Config.NOTIFICATION_HOURS:
                    notification_time = event_datetime - timedelta(hours=hours_before)
                    
                    # Проверяем, нужно ли отправить уведомление сейчас
                    # (в пределах 1 минуты от времени уведомления)
                    time_diff = abs((current_time - notification_time).total_seconds())
                    
                    if time_diff <= 60:  # 1 минута погрешности
                        await NotificationService.send_upcoming_event_notification(
                            event, hours_before, bot
                        )
            except Exception as e:
                print(f"Ошибка при проверке мероприятия {event.id}: {e}")
    
    @staticmethod
    async def send_notification(user_ids: List[int], message: str, bot: Bot):
        """
        Отправляет произвольное уведомление списку пользователей.
        
        Args:
            user_ids: Список ID пользователей
            message: Текст сообщения
            bot: Экземпляр бота
        """
        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления пользователю {user_id}: {e}")

