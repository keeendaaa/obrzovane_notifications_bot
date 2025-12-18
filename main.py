"""
Главный файл для запуска Telegram-бота.
Инициализирует бота, базу данных, обработчики и планировщик уведомлений.
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import Config
from database import db
from handlers.start import register_start_handlers
from handlers.admin import register_admin_handlers
from handlers.notifications import register_notification_handlers
from utils.scheduler import NotificationScheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """
    Функция, выполняемая при запуске бота.
    Инициализирует базу данных и отправляет сообщение администраторам.
    """
    logger.info("🚀 Запуск бота...")
    
    # Инициализируем базу данных
    await db.init_db()
    logger.info("✅ База данных инициализирована")
    
    # Отправляем уведомление администраторам о запуске
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "✅ Бот успешно запущен и готов к работе!"
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение администратору {admin_id}: {e}")


async def on_shutdown(bot: Bot):
    """
    Функция, выполняемая при остановке бота.
    Закрывает соединение с базой данных.
    """
    logger.info("⏹ Остановка бота...")
    await db.close()
    logger.info("✅ Соединение с базой данных закрыто")


async def main():
    """
    Главная функция для запуска бота.
    Инициализирует все компоненты и запускает polling.
    """
    # Валидируем конфигурацию
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        return
    
    # Инициализируем бота и диспетчер
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем обработчики
    register_start_handlers(dp)
    register_admin_handlers(dp)
    register_notification_handlers(dp)
    
    # Инициализируем планировщик уведомлений
    scheduler = NotificationScheduler(bot)
    scheduler.start()
    
    # Регистрируем функции запуска и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        # Запускаем бота
        logger.info("🔄 Запуск polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"❌ Ошибка при работе бота: {e}")
    finally:
        # Останавливаем планировщик
        scheduler.stop()
        await bot.session.close()


if __name__ == "__main__":
    """
    Точка входа в приложение.
    Запускает асинхронную функцию main().
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

