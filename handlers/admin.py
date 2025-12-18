"""
Обработчики админ-панели для управления мероприятиями.
Использует FSM (Finite State Machine) для пошагового ввода данных.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from typing import Optional
from config import Config
from models.event import Event
from models.user import User
from keyboards.inline import get_event_keyboard, get_events_list_keyboard, get_confirm_keyboard
from keyboards.reply import get_admin_keyboard
from services.notification_service import NotificationService

router = Router()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in Config.ADMIN_IDS


# FSM состояния для добавления мероприятия
class AddEventStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_datetime = State()
    waiting_for_location = State()
    waiting_for_format = State()
    waiting_for_link = State()
    waiting_for_photo = State()


# FSM состояния для редактирования мероприятия
class EditEventStates(StatesGroup):
    waiting_for_event_id = State()
    waiting_for_field = State()
    waiting_for_new_value = State()


# FSM состояния для удаления мероприятия
class DeleteEventStates(StatesGroup):
    waiting_for_event_id = State()
    waiting_for_confirmation = State()


@router.message(Command("add_event"))
async def cmd_add_event(message: Message, state: FSMContext):
    """
    Начинает процесс добавления нового мероприятия.
    Использует FSM для пошагового ввода данных.
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    await state.set_state(AddEventStates.waiting_for_title)
    await message.answer(
        "➕ <b>Добавление нового мероприятия</b>\n\n"
        "Шаг 1/7: Введите <b>название</b> мероприятия:",
        parse_mode="HTML"
    )


@router.message(AddEventStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Обрабатывает название мероприятия"""
    await state.update_data(title=message.text)
    await state.set_state(AddEventStates.waiting_for_description)
    await message.answer(
        "Шаг 2/7: Введите <b>описание</b> мероприятия\n"
        "(или отправьте '-' чтобы пропустить):",
        parse_mode="HTML"
    )


@router.message(AddEventStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обрабатывает описание мероприятия"""
    description = message.text if message.text != "-" else ""
    await state.update_data(description=description)
    await state.set_state(AddEventStates.waiting_for_datetime)
    await message.answer(
        "Шаг 3/7: Введите <b>дату и время</b> мероприятия\n"
        "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Пример: 25.12.2024 18:00",
        parse_mode="HTML"
    )


@router.message(AddEventStates.waiting_for_datetime)
async def process_datetime(message: Message, state: FSMContext):
    """Обрабатывает дату и время мероприятия"""
    try:
        # Парсим дату в формате ДД.ММ.ГГГГ ЧЧ:ММ
        dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        event_datetime = dt.isoformat()
        await state.update_data(event_datetime=event_datetime)
        await state.set_state(AddEventStates.waiting_for_location)
        await message.answer(
            "Шаг 4/7: Введите <b>место проведения</b>\n"
            "(или отправьте '-' чтобы пропустить):",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Пример: 25.12.2024 18:00"
        )


@router.message(AddEventStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext):
    """Обрабатывает место проведения"""
    location = message.text if message.text != "-" else ""
    await state.update_data(location=location)
    await state.set_state(AddEventStates.waiting_for_format)
    await message.answer(
        "Шаг 5/7: Выберите <b>формат</b> мероприятия:\n"
        "Отправьте: online, offline или hybrid",
        parse_mode="HTML"
    )


@router.message(AddEventStates.waiting_for_format)
async def process_format(message: Message, state: FSMContext):
    """Обрабатывает формат мероприятия"""
    format_text = message.text.lower()
    if format_text not in ["online", "offline", "hybrid"]:
        await message.answer(
            "❌ Неверный формат. Используйте: online, offline или hybrid"
        )
        return
    
    await state.update_data(format=format_text)
    await state.set_state(AddEventStates.waiting_for_link)
    await message.answer(
        "Шаг 6/7: Введите <b>ссылку</b> на мероприятие\n"
        "(или отправьте '-' чтобы пропустить):",
        parse_mode="HTML"
    )


@router.message(AddEventStates.waiting_for_link)
async def process_link(message: Message, state: FSMContext):
    """Обрабатывает ссылку и переходит к загрузке фото"""
    link = message.text if message.text != "-" else ""
    await state.update_data(link=link)
    await state.set_state(AddEventStates.waiting_for_photo)
    await message.answer(
        "Шаг 7/7: Отправьте <b>фото</b> для мероприятия\n"
        "(или отправьте '-' чтобы пропустить):",
        parse_mode="HTML"
    )


@router.message(AddEventStates.waiting_for_photo)
async def process_photo(message: Message, state: FSMContext):
    """Обрабатывает фото и завершает создание мероприятия"""
    from aiogram.types import PhotoSize
    
    photo_file_id = ""
    
    # Проверяем, есть ли фото в сообщении
    if message.text and message.text == "-":
        # Пользователь пропустил загрузку фото
        photo_file_id = ""
    elif message.photo:
        # Получаем file_id самого большого фото
        photo_file_id = message.photo[-1].file_id
    else:
        # Если не фото и не "-", просим отправить фото или "-"
        await message.answer(
            "❌ Пожалуйста, отправьте фото или '-' чтобы пропустить"
        )
        return
    
    data = await state.get_data()
    
    # Создаем мероприятие
    event = Event(
        title=data["title"],
        description=data.get("description", ""),
        event_datetime=data["event_datetime"],
        location=data.get("location", ""),
        format=data.get("format", "offline"),
        link=data.get("link", ""),
        photo_file_id=photo_file_id
    )
    
    event_id = await event.save()
    
    await state.clear()
    
    # Отправляем подтверждение с фото, если оно есть
    if photo_file_id:
        await message.answer_photo(
            photo=photo_file_id,
            caption=f"✅ Мероприятие успешно добавлено!\n\n{event.format_message()}",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"✅ Мероприятие успешно добавлено!\n\n{event.format_message()}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    
    # Отправляем уведомления подписанным пользователям
    await NotificationService.send_new_event_notification(event, message.bot)


@router.message(Command("list_events"))
async def cmd_list_events(message: Message):
    """Показывает список всех мероприятий администратору"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    events = await Event.get_all()
    
    if not events:
        await message.answer("📋 Пока нет мероприятий.")
        return
    
    # Показываем первое мероприятие
    first_event = events[0]
    caption = f"📋 <b>Все мероприятия ({len(events)})</b>\n\n{first_event.format_message()}"
    
    if first_event.photo_file_id:
        await message.answer_photo(
            photo=first_event.photo_file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_event_keyboard(first_event.id, show_delete=True)
        )
    else:
        await message.answer(
            caption,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=get_event_keyboard(first_event.id, show_delete=True)
        )
    
    # Если мероприятий больше одного, показываем список
    if len(events) > 1:
        await message.answer(
            "Выберите мероприятие для управления:",
            reply_markup=get_events_list_keyboard(events, page=0)
        )


@router.message(Command("edit_event"))
async def cmd_edit_event(message: Message, state: FSMContext):
    """Начинает процесс редактирования мероприятия"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    await state.set_state(EditEventStates.waiting_for_event_id)
    await message.answer(
        "✏️ <b>Редактирование мероприятия</b>\n\n"
        "Введите ID мероприятия, которое хотите отредактировать:",
        parse_mode="HTML"
    )


@router.message(EditEventStates.waiting_for_event_id)
async def process_edit_event_id(message: Message, state: FSMContext):
    """Обрабатывает ID мероприятия для редактирования"""
    try:
        event_id = int(message.text)
        event = await Event.get_by_id(event_id)
        
        if not event:
            await message.answer("❌ Мероприятие с таким ID не найдено.")
            await state.clear()
            return
        
        await state.update_data(event_id=event_id)
        await state.set_state(EditEventStates.waiting_for_field)
        
        # Отправляем фото мероприятия, если оно есть
        if event.photo_file_id:
            await message.answer_photo(
                photo=event.photo_file_id,
                caption=f"📝 Редактирование мероприятия:\n\n{event.format_message()}\n\n"
                        "Какое поле вы хотите изменить?\n"
                        "Доступные поля:\n"
                        "• title - название\n"
                        "• description - описание\n"
                        "• datetime - дата и время\n"
                        "• location - место\n"
                        "• format - формат (online/offline/hybrid)\n"
                        "• link - ссылка\n"
                        "• photo - фото",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"📝 Редактирование мероприятия:\n\n{event.format_message()}\n\n"
                "Какое поле вы хотите изменить?\n"
                "Доступные поля:\n"
                "• title - название\n"
                "• description - описание\n"
                "• datetime - дата и время\n"
                "• location - место\n"
                "• format - формат (online/offline/hybrid)\n"
                "• link - ссылка\n"
                "• photo - фото",
                parse_mode="HTML",
                disable_web_page_preview=True
            )
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число.")


@router.message(EditEventStates.waiting_for_field)
async def process_edit_field(message: Message, state: FSMContext):
    """Обрабатывает выбор поля для редактирования"""
    field = message.text.lower()
    valid_fields = ["title", "description", "datetime", "location", "format", "link", "photo"]
    
    if field not in valid_fields:
        await message.answer(
            f"❌ Неверное поле. Используйте одно из: {', '.join(valid_fields)}"
        )
        return
    
    await state.update_data(field=field)
    await state.set_state(EditEventStates.waiting_for_new_value)
    
    if field == "photo":
        await message.answer(
            "📷 Отправьте новое фото для мероприятия\n"
            "(или отправьте '-' чтобы удалить фото)"
        )
    else:
        field_prompts = {
            "title": "Введите новое название:",
            "description": "Введите новое описание:",
            "datetime": "Введите новую дату и время (ДД.ММ.ГГГГ ЧЧ:ММ):",
            "location": "Введите новое место:",
            "format": "Введите новый формат (online/offline/hybrid):",
            "link": "Введите новую ссылку:"
        }
        await message.answer(field_prompts[field])


@router.message(EditEventStates.waiting_for_new_value)
async def process_edit_value(message: Message, state: FSMContext):
    """Обрабатывает новое значение поля и сохраняет изменения"""
    data = await state.get_data()
    event_id = data["event_id"]
    field = data["field"]
    
    event = await Event.get_by_id(event_id)
    if not event:
        await message.answer("❌ Мероприятие не найдено.")
        await state.clear()
        return
    
    # Обработка фото
    if field == "photo":
        if message.text and message.text == "-":
            # Удаляем фото
            new_value = ""
        elif message.photo:
            # Получаем file_id самого большого фото
            new_value = message.photo[-1].file_id
        else:
            await message.answer(
                "❌ Пожалуйста, отправьте фото или '-' чтобы удалить фото"
            )
            return
    else:
        # Для других полей проверяем, что это текст, а не фото
        if message.photo:
            await message.answer(
                f"❌ Для поля '{field}' нужно отправить текст, а не фото"
            )
            return
        new_value = message.text
    
    # Обработка специальных полей
    if field == "datetime":
        try:
            dt = datetime.strptime(new_value, "%d.%m.%Y %H:%M")
            new_value = dt.isoformat()
        except ValueError:
            await message.answer(
                "❌ Неверный формат даты. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ"
            )
            return
    
    if field == "format" and new_value.lower() not in ["online", "offline", "hybrid"]:
        await message.answer("❌ Неверный формат. Используйте: online, offline или hybrid")
        return
    
    # Обновляем поле
    setattr(event, field, new_value)
    await event.save()
    
    await state.clear()
    
    # Отправляем подтверждение с фото, если оно есть
    if event.photo_file_id:
        await message.answer_photo(
            photo=event.photo_file_id,
            caption=f"✅ Поле '{field}' успешно обновлено!\n\n{event.format_message()}",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"✅ Поле '{field}' успешно обновлено!\n\n{event.format_message()}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )


@router.message(Command("delete_event"))
async def cmd_delete_event(message: Message, state: FSMContext):
    """Начинает процесс удаления мероприятия"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    await state.set_state(DeleteEventStates.waiting_for_event_id)
    await message.answer(
        "🗑 <b>Удаление мероприятия</b>\n\n"
        "Введите ID мероприятия, которое хотите удалить:",
        parse_mode="HTML"
    )


@router.message(DeleteEventStates.waiting_for_event_id)
async def process_delete_event_id(message: Message, state: FSMContext):
    """Обрабатывает ID мероприятия для удаления"""
    try:
        event_id = int(message.text)
        event = await Event.get_by_id(event_id)
        
        if not event:
            await message.answer("❌ Мероприятие с таким ID не найдено.")
            await state.clear()
            return
        
        await state.update_data(event_id=event_id)
        await state.set_state(DeleteEventStates.waiting_for_confirmation)
        
        confirmation_text = f"⚠️ Вы уверены, что хотите удалить это мероприятие?\n\n{event.format_message()}"
        
        if event.photo_file_id:
            await message.answer_photo(
                photo=event.photo_file_id,
                caption=confirmation_text,
                parse_mode="HTML",
                reply_markup=get_confirm_keyboard("delete", event_id)
            )
        else:
            await message.answer(
                confirmation_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=get_confirm_keyboard("delete", event_id)
            )
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число.")


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_event(callback: CallbackQuery, state: FSMContext):
    """Подтверждает удаление мероприятия"""
    event_id = int(callback.data.split("_")[-1])
    event = await Event.get_by_id(event_id)
    
    if event:
        await event.delete()
        await callback.message.edit_text("✅ Мероприятие успешно удалено!")
        await callback.answer("Мероприятие удалено")
    else:
        await callback.answer("Мероприятие не найдено", show_alert=True)
    
    await state.clear()


@router.callback_query(F.data.startswith("cancel_delete_"))
async def cancel_delete_event(callback: CallbackQuery, state: FSMContext):
    """Отменяет удаление мероприятия"""
    await callback.message.edit_text("❌ Удаление отменено.")
    await callback.answer("Удаление отменено")
    await state.clear()


@router.message(Command("send_test_notification"))
async def cmd_send_test_notification(message: Message):
    """Отправляет тестовое уведомление администратору"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    test_text = (
        "🧪 <b>Тестовое уведомление</b>\n\n"
        "Это тестовое сообщение для проверки работы системы уведомлений.\n"
        "Если вы видите это сообщение, значит бот работает корректно!"
    )
    
    await message.answer(test_text, parse_mode="HTML")
    
    # Также можно отправить всем подписанным пользователям
    subscribed_users = await User.get_subscribed_users()
    if subscribed_users:
        await message.answer(
            f"📊 Всего подписанных пользователей: {len(subscribed_users)}\n"
            "Используйте эту команду для проверки отправки уведомлений."
        )


@router.message(Command("stats"))
@router.message(Command("analytics"))
async def cmd_stats(message: Message):
    """
    Показывает аналитику об использовании бота.
    Доступно только администраторам.
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    # Получаем статистику по пользователям
    total_users = await User.get_all_users_count()
    subscribed_users = await User.get_subscribed_count()
    unsubscribed_users = await User.get_unsubscribed_count()
    new_users_7d = await User.get_recent_users_count(7)
    new_users_30d = await User.get_recent_users_count(30)
    
    # Получаем статистику по мероприятиям
    total_events = await Event.get_all_count()
    upcoming_events = await Event.get_upcoming_count()
    past_events = await Event.get_past_count()
    new_events_7d = await Event.get_recent_events_count(7)
    new_events_30d = await Event.get_recent_events_count(30)
    
    # Статистика по форматам
    format_stats = await Event.get_by_format_stats()
    
    # Статистика по уведомлениям
    from database import db
    notifications_sent = await db.fetch_one("SELECT COUNT(*) FROM sent_notifications")
    notifications_count = notifications_sent[0] if notifications_sent else 0
    
    # Вычисляем процент подписки
    subscription_rate = (subscribed_users / total_users * 100) if total_users > 0 else 0
    
    # Формируем сообщение
    stats_text = (
        "📊 <b>Аналитика использования бота</b>\n\n"
        
        "👥 <b>Пользователи:</b>\n"
        f"• Всего пользователей: <b>{total_users}</b>\n"
        f"• Подписаны: <b>{subscribed_users}</b> ({subscription_rate:.1f}%)\n"
        f"• Не подписаны: <b>{unsubscribed_users}</b>\n"
        f"• Новых за 7 дней: <b>{new_users_7d}</b>\n"
        f"• Новых за 30 дней: <b>{new_users_30d}</b>\n\n"
        
        "📅 <b>Мероприятия:</b>\n"
        f"• Всего мероприятий: <b>{total_events}</b>\n"
        f"• Предстоящих: <b>{upcoming_events}</b>\n"
        f"• Прошедших: <b>{past_events}</b>\n"
        f"• Создано за 7 дней: <b>{new_events_7d}</b>\n"
        f"• Создано за 30 дней: <b>{new_events_30d}</b>\n\n"
        
        "🎯 <b>Форматы мероприятий:</b>\n"
        f"• Онлайн: <b>{format_stats['online']}</b>\n"
        f"• Офлайн: <b>{format_stats['offline']}</b>\n"
        f"• Гибрид: <b>{format_stats['hybrid']}</b>\n"
        f"• Другие: <b>{format_stats['other']}</b>\n\n"
        
        "🔔 <b>Уведомления:</b>\n"
        f"• Отправлено напоминаний: <b>{notifications_count}</b>\n"
    )
    
    await message.answer(stats_text, parse_mode="HTML")


@router.callback_query(F.data.startswith("delete_event_"))
async def callback_delete_event(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки удаления мероприятия"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    event_id = int(callback.data.split("_")[-1])
    event = await Event.get_by_id(event_id)
    
    if event:
        await state.update_data(event_id=event_id)
        await state.set_state(DeleteEventStates.waiting_for_confirmation)
        
        confirmation_text = f"⚠️ Вы уверены, что хотите удалить это мероприятие?\n\n{event.format_message()}"
        
        # Если есть фото, отправляем новое сообщение с фото
        if event.photo_file_id:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=event.photo_file_id,
                caption=confirmation_text,
                parse_mode="HTML",
                reply_markup=get_confirm_keyboard("delete", event_id)
            )
        else:
            await callback.message.edit_text(
                confirmation_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=get_confirm_keyboard("delete", event_id)
            )
    
    await callback.answer()


@router.callback_query(F.data.startswith("edit_event_"))
async def callback_edit_event(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки редактирования мероприятия"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    event_id = int(callback.data.split("_")[-1])
    event = await Event.get_by_id(event_id)
    
    if event:
        await state.update_data(event_id=event_id)
        await state.set_state(EditEventStates.waiting_for_field)
        
        edit_text = (
            f"📝 Редактирование мероприятия:\n\n{event.format_message()}\n\n"
            "Какое поле вы хотите изменить?\n"
            "Доступные поля:\n"
            "• title - название\n"
            "• description - описание\n"
            "• datetime - дата и время\n"
            "• location - место\n"
            "• format - формат (online/offline/hybrid)\n"
            "• link - ссылка\n"
            "• photo - фото"
        )
        
        # Если есть фото, отправляем новое сообщение с фото
        if event.photo_file_id:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=event.photo_file_id,
                caption=edit_text,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                edit_text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
    
    await callback.answer()


def register_admin_handlers(dp):
    """Регистрирует все обработчики админ-панели"""
    dp.include_router(router)

