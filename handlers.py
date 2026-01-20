"""
Модуль обработчиков команд и кнопок для интерактивного бота.
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from config import logger
from schedule_generator import generate_schedule_for_subscribers


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
        InlineKeyboardButton("📅 Получить календарь", callback_data="get_schedule")
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
        "/status - Статус подписки\n"
        "/schedule - Получить календарь на текущую неделю\n\n"
        "<b>Что я умею:</b>\n"
        "• Автоматическая рассылка в каналы (11:00, 13:00, 16:00 МСК)\n"
        "• Еженедельное расписание по понедельникам в 10:00 МСК\n"
        "• Отправка Excel файлов с календарем коммуникаций\n"
        "• Генерация календаря по запросу в любой день\n\n"
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
            "Чтобы отписаться, используйте /start\n\n"
            "💡 <b>Совет:</b> Используйте /schedule чтобы получить календарь прямо сейчас!"
        )
    else:
        status_text += "Чтобы подписаться, используйте /start"
    
    await update.message.reply_text(status_text, parse_mode='HTML')


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /schedule - отправка календаря по запросу."""
    user_id = update.effective_user.id
    user = update.effective_user
    
    logger.info(f"Запрос календаря от пользователя {user_id} (@{user.username})")
    
    # Отправить сообщение о генерации
    status_message = await update.message.reply_text(
        "⏳ Генерирую календарь на текущую неделю...",
        parse_mode='HTML'
    )
    
    try:
        # Сгенерировать календарь
        schedule_file = generate_schedule_for_subscribers()
        logger.info(f"Календарь создан: {schedule_file}")
        
        # Текст сообщения
        message_text = (
            "📅 <b>Календарь коммуникаций на текущую неделю</b>\n\n"
            "Высылаю вам актуальный план публикаций.\n\n"
            "В файле вы найдете:\n"
            "• Даты и время всех публикаций\n"
            "• Названия сообщений\n"
            "• Информацию о медиа файлах\n\n"
            "📊 Приятного просмотра!"
        )
        
        # Отправить файл
        with open(schedule_file, 'rb') as file:
            await update.message.reply_document(
                document=file,
                caption=message_text,
                parse_mode='HTML',
                filename=f"calendar_{os.path.basename(schedule_file)}"
            )
        
        # Удалить сообщение о генерации
        await status_message.delete()
        
        logger.info(f"Календарь отправлен пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации/отправке календаря пользователю {user_id}: {e}")
        
        await status_message.edit_text(
            "❌ Произошла ошибка при генерации календаря. "
            "Попробуйте позже или обратитесь в поддержку.",
            parse_mode='HTML'
        )


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
    
    elif data == "get_schedule":
        # Отправить календарь
        await query.answer("⏳ Генерирую календарь...")
        
        user_id = user.id
        logger.info(f"Запрос календаря через кнопку от пользователя {user_id} (@{user.username})")
        
        try:
            # Сгенерировать календарь
            schedule_file = generate_schedule_for_subscribers()
            logger.info(f"Календарь создан: {schedule_file}")
            
            # Текст сообщения
            message_text = (
                "📅 <b>Календарь коммуникаций на текущую неделю</b>\n\n"
                "Высылаю вам актуальный план публикаций.\n\n"
                "В файле вы найдете:\n"
                "• Даты и время всех публикаций\n"
                "• Названия сообщений\n"
                "• Информацию о медиа файлах\n\n"
                "📊 Приятного просмотра!"
            )
            
            # Отправить файл
            with open(schedule_file, 'rb') as file:
                await query.message.reply_document(
                    document=file,
                    caption=message_text,
                    parse_mode='HTML',
                    filename=f"calendar_{os.path.basename(schedule_file)}"
                )
            
            logger.info(f"Календарь отправлен пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при генерации/отправке календаря пользователю {user_id}: {e}")
            
            await query.message.reply_text(
                "❌ Произошла ошибка при генерации календаря. "
                "Попробуйте позже или обратитесь в поддержку.",
                parse_mode='HTML'
            )
    
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
            "<b>Календарь по запросу:</b>\n"
            "• Получите календарь в любой момент\n"
            "• Используйте кнопку '📅 Получить календарь'\n"
            "• Или команду /schedule\n\n"
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
