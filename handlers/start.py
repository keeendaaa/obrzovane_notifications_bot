"""
Обработчики стартовых команд и базового взаимодействия с пользователями.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from models.user import User
from keyboards.inline import get_subscribe_keyboard
from keyboards.reply import get_main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start.
    Приветствует пользователя и предлагает подписаться на уведомления.
    """
    # Получаем или создаем пользователя
    user = await User.get_or_create(message.from_user.id)
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для уведомлений о мероприятиях сообщества.\n\n"
        "Я буду присылать тебе уведомления о:\n"
        "• Новых мероприятиях\n"
        "• Предстоящих событиях (напоминания)\n\n"
        "Используй кнопки ниже для просмотра мероприятий."
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )
    
    # Отправляем сообщение с кнопкой подписки
    status_text = "✅ Вы подписаны на уведомления" if user.is_subscribed else "❌ Вы не подписаны на уведомления"
    await message.answer(
        status_text,
        reply_markup=get_subscribe_keyboard(user.is_subscribed)
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help.
    Показывает справку по использованию бота.
    """
    help_text = (
        "📖 <b>Справка по использованию бота</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/subscribe - Подписаться на уведомления\n"
        "/unsubscribe - Отписаться от уведомлений\n\n"
        "<b>Управление подпиской:</b>\n"
        "Используй кнопки под сообщениями или команды выше для управления подпиской.\n\n"
        "Бот автоматически присылает уведомления о новых и предстоящих мероприятиях."
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    """Обработчик команды /subscribe"""
    user = await User.get_or_create(message.from_user.id)
    await user.subscribe()
    
    await message.answer(
        "✅ Вы успешно подписались на уведомления!",
        reply_markup=get_subscribe_keyboard(True)
    )


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    """Обработчик команды /unsubscribe"""
    user = await User.get_or_create(message.from_user.id)
    await user.unsubscribe()
    
    await message.answer(
        "❌ Вы отписались от уведомлений.",
        reply_markup=get_subscribe_keyboard(False)
    )


@router.callback_query(F.data == "subscribe")
async def callback_subscribe(callback: CallbackQuery):
    """Обработчик нажатия на кнопку подписки"""
    user = await User.get_or_create(callback.from_user.id)
    await user.subscribe()
    
    await callback.answer("✅ Вы подписались на уведомления!")
    await callback.message.edit_text(
        "✅ Вы подписаны на уведомления",
        reply_markup=get_subscribe_keyboard(True)
    )


@router.callback_query(F.data == "unsubscribe")
async def callback_unsubscribe(callback: CallbackQuery):
    """Обработчик нажатия на кнопку отписки"""
    user = await User.get_or_create(callback.from_user.id)
    await user.unsubscribe()
    
    await callback.answer("❌ Вы отписались от уведомлений")
    await callback.message.edit_text(
        "❌ Вы не подписаны на уведомления",
        reply_markup=get_subscribe_keyboard(False)
    )


def register_start_handlers(dp):
    """Регистрирует все обработчики стартовых команд"""
    dp.include_router(router)

