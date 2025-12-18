"""
Планировщик задач для автоматической отправки уведомлений.
Использует APScheduler для периодической проверки мероприятий.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot
from services.notification_service import NotificationService


class NotificationScheduler:
    """
    Планировщик для автоматической отправки уведомлений.
    Проверяет предстоящие мероприятия каждую минуту.
    """
    
    def __init__(self, bot: Bot):
        """
        Инициализирует планировщик.
        
        Args:
            bot: Экземпляр бота для отправки сообщений
        """
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Запускает планировщик"""
        # Проверяем мероприятия каждую минуту
        self.scheduler.add_job(
            self._check_reminders,
            trigger=IntervalTrigger(minutes=1),
            id="check_reminders",
            replace_existing=True
        )
        self.scheduler.start()
        print("✅ Планировщик уведомлений запущен")
    
    def stop(self):
        """Останавливает планировщик"""
        self.scheduler.shutdown()
        print("⏹ Планировщик уведомлений остановлен")
    
    async def _check_reminders(self):
        """Внутренний метод для проверки и отправки напоминаний"""
        try:
            await NotificationService.check_and_send_reminders(self.bot)
        except Exception as e:
            print(f"Ошибка в планировщике уведомлений: {e}")

