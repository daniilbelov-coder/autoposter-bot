"""
Модуль обработчиков команд и кнопок для интерактивного бота.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from config import logger


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.
    Показывает приветствие и кнопки управления.
    """
    user = update.effective_user
    user_id = user.id
    
    # Проверить статус подписки
    is_subscribed = db.is_subscribed(user_id)
    
    # Создать клавиатуру
    keyboard = []
    
    if is_subscribed:
        keyboard.append([
            InlineKeyboardButton("✅ Вы подписаны", callback_data="subscribed"),
            InlineKeyboardButton("❌ Отписаться", callback_data="unsubscribe")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("📅 Подписаться на расписание", callback_data="subscribe")
        ])
    
    keyboard.append([
        InlineKeyboardButton("ℹ️ Информация", callback_data="info")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"🤖 Я бот для автоматической рассылки сообщений в каналы.\n\n"
        f"📅 <b>Еженедельное расписание:</b>\n"
        f"Каждый понедельник в 10:00 МСК я буду присылать тебе "
        f"календарь коммуникаций на неделю с планом публикаций.\n\n"
        f"📊 <b>Формат:</b> Excel файл (.xlsx)\n\n"
    )
    
    if is_subscribed:
        welcome_text += "✅ <b>Вы подписаны на рассылку!</b>"
    else:
        welcome_text += "Нажми кнопку ниже, чтобы подписаться."
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    logger.info(f"Команда /start от пользователя {user_id} (@{user.username})")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
    help_text = (
        "📖 <b>Помощь</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/status - Статус подписки\n\n"
        "<b>Что я умею:</b>\n"
        "• Автоматическая рассылка в каналы (11:00, 13:00, 16:00 МСК)\n"
        "• Еженедельное расписание по понедельникам в 10:00 МСК\n"
        "• Отправка Excel файлов с календарем коммуникаций\n\n"
        "<b>Подписка:</b>\n"
        "Нажми /start и выбери 'Подписаться на расписание'"
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status."""
    user_id = update.effective_user.id
    is_subscribed = db.is_subscribed(user_id)
    total_subscribers = db.get_subscribers_count()
    
    status_text = (
        "📊 <b>Ваш статус</b>\n\n"
        f"Подписка: {'✅ Активна' if is_subscribed else '❌ Не активна'}\n"
        f"Всего подписчиков: {total_subscribers}\n\n"
    )
    
    if is_subscribed:
        status_text += (
            "📅 Следующее расписание придёт в понедельник в 10:00 МСК\n\n"
            "Чтобы отписаться, используйте /start"
        )
    else:
        status_text += "Чтобы подписаться, используйте /start"
    
    await update.message.reply_text(status_text, parse_mode='HTML')


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    data = query.data
    
    if data == "subscribe":
        # Подписать пользователя
        success = db.add_subscriber(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        if success:
            response_text = (
                "✅ <b>Вы успешно подписаны!</b>\n\n"
                "📅 Каждый понедельник в 10:00 МСК вы будете получать "
                "календарь коммуникаций на неделю в формате Excel.\n\n"
                "📊 В календаре будет план всех публикаций с датами и временем.\n\n"
                "Используйте /start чтобы управлять подпиской."
            )
            
            # Обновить клавиатуру
            keyboard = [
                [
                    InlineKeyboardButton("✅ Вы подписаны", callback_data="subscribed"),
                    InlineKeyboardButton("❌ Отписаться", callback_data="unsubscribe")
                ],
                [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            logger.info(f"Пользователь {user_id} подписался")
        else:
            await query.edit_message_text("❌ Ошибка при подписке. Попробуйте позже.")
    
    elif data == "unsubscribe":
        # Отписать пользователя
        success = db.remove_subscriber(user_id)
        
        if success:
            response_text = (
                "✅ Вы успешно отписаны от рассылки.\n\n"
                "Чтобы подписаться снова, используйте /start"
            )
            
            keyboard = [
                [InlineKeyboardButton("📅 Подписаться снова", callback_data="subscribe")],
                [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            logger.info(f"Пользователь {user_id} отписался")
        else:
            await query.edit_message_text("❌ Ошибка при отписке.")
    
    elif data == "subscribed":
        # Показать информацию о подписке
        await query.answer("✅ Вы уже подписаны на рассылку!")
    
    elif data == "info":
        # Показать информацию о боте
        info_text = (
            "ℹ️ <b>Информация о боте</b>\n\n"
            "<b>Автоматическая рассылка в каналы:</b>\n"
            "• 11:00 МСК\n"
            "• 13:00 МСК\n"
            "• 16:00 МСК\n\n"
            "<b>Еженедельное расписание:</b>\n"
            "• Понедельник, 10:00 МСК\n"
            "• Формат: Excel (.xlsx)\n"
            "• Содержит план публикаций на неделю\n\n"
            "<b>Умный выбор сообщений:</b>\n"
            "• Учитывает частоту публикаций\n"
            "• Избегает конфликтов между сообщениями\n"
            "• Разнообразие контента\n\n"
            "Используйте /help для справки"
        )
        
        await query.answer()
        await query.edit_message_text(info_text, parse_mode='HTML')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок."""
    logger.error(f"Ошибка при обработке update: {context.error}", exc_info=context.error)
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке вашего запроса. "
                "Попробуйте позже или используйте /start"
            )
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
