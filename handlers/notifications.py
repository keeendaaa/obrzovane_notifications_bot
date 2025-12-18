"""
Обработчики для просмотра мероприятий пользователями.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from models.event import Event
from keyboards.inline import get_events_list_keyboard

router = Router()


@router.message(F.text == "📅 Предстоящие мероприятия")
async def show_upcoming_events(message: Message):
    """
    Показывает список предстоящих мероприятий пользователю.
    """
    events = await Event.get_upcoming()
    
    if not events:
        await message.answer(
            "📅 Пока нет предстоящих мероприятий.\n"
            "Следите за обновлениями!"
        )
        return
    
    # Показываем первое мероприятие
    first_event = events[0]
    if first_event.photo_file_id:
        await message.answer_photo(
            photo=first_event.photo_file_id,
            caption=first_event.format_message(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            first_event.format_message(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    
    # Если мероприятий больше одного, показываем список
    if len(events) > 1:
        await message.answer(
            f"📋 Всего предстоящих мероприятий: {len(events)}\n"
            "Выберите мероприятие для просмотра:",
            reply_markup=get_events_list_keyboard(events, page=0)
        )


@router.callback_query(F.data.startswith("view_event_"))
async def view_event(callback: CallbackQuery):
    """Показывает детали конкретного мероприятия"""
    event_id = int(callback.data.split("_")[-1])
    event = await Event.get_by_id(event_id)
    
    if event:
        # Если есть фото, отправляем новое сообщение с фото
        # (нельзя редактировать сообщение на фото)
        if event.photo_file_id:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=event.photo_file_id,
                caption=event.format_message(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                event.format_message(),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
    else:
        await callback.answer("Мероприятие не найдено", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("events_page_"))
async def navigate_events_page(callback: CallbackQuery):
    """Обработка пагинации списка мероприятий"""
    page = int(callback.data.split("_")[-1])
    events = await Event.get_upcoming()
    
    if events:
        await callback.message.edit_reply_markup(
            reply_markup=get_events_list_keyboard(events, page=page)
        )
    
    await callback.answer()


def register_notification_handlers(dp):
    """Регистрирует все обработчики для просмотра мероприятий"""
    dp.include_router(router)

