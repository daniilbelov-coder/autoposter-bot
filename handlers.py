"""
Модуль обработчиков команд и кнопок для интерактивного бота.
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from database import db
from config import logger, ADMIN_PASSWORD
from schedule_generator import generate_schedule_for_subscribers
from message_selector import selector

# Состояния для админ-диалога
ADMIN_PASSWORD_STATE = 1
ADMIN_POST_SELECTION_STATE = 2
ADMIN_CHANNEL_SELECTION_STATE = 3
ADMIN_PREVIEW_STATE = 4


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
        InlineKeyboardButton("📤 Отправить пост (Админ)", callback_data="admin_send_post")
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


async def admin_send_post_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Отправить пост (Админ)'."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    logger.info(f"Запрос админ-панели от пользователя {user_id} (@{user.username})")
    
    # Проверить, установлен ли пароль
    if not ADMIN_PASSWORD:
        await query.message.reply_text(
            "❌ Админ-функция недоступна: пароль не установлен в настройках бота.",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    # Запросить пароль
    await query.message.reply_text(
        "🔐 <b>Админ-панель</b>\n\n"
        "Введите пароль администратора для доступа к функции ручной отправки постов:\n\n"
        "Для отмены используйте /cancel",
        parse_mode='HTML'
    )
    
    return ADMIN_PASSWORD_STATE


async def admin_check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка пароля администратора."""
    user = update.effective_user
    user_id = user.id
    password = update.message.text.strip()
    
    # Проверить пароль
    if password != ADMIN_PASSWORD:
        logger.warning(f"Неверный пароль от пользователя {user_id} (@{user.username})")
        
        await update.message.reply_text(
            "❌ <b>Неверный пароль!</b>\n\n"
            "Доступ запрещен. Возвращаемся в главное меню.\n\n"
            "Используйте /start для возврата в меню.",
            parse_mode='HTML'
        )
        
        return ConversationHandler.END
    
    # Пароль верный - показать список постов
    logger.info(f"Успешная авторизация пользователя {user_id} (@{user.username})")
    
    messages = selector.messages
    
    if not messages:
        await update.message.reply_text(
            "❌ <b>Ошибка:</b> Список постов пуст!",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    # Формирование списка постов
    post_list = "🔐 <b>Админ-панель: Выбор поста для отправки</b>\n\n"
    post_list += "Введите номер поста, который хотите отправить:\n\n"
    
    for idx, message in enumerate(messages, 1):
        title = message['title']
        # Ограничить длину заголовка для удобства
        if len(title) > 60:
            title = title[:57] + "..."
        post_list += f"{idx}. {title}\n"
    
    post_list += f"\n<b>Всего постов:</b> {len(messages)}\n\n"
    post_list += "Для отмены используйте /cancel"
    
    # Сохранить количество постов в контексте
    context.user_data['admin_total_posts'] = len(messages)
    
    await update.message.reply_text(post_list, parse_mode='HTML')
    
    return ADMIN_POST_SELECTION_STATE


async def admin_select_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор поста по номеру - показать превью."""
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()
    
    # Парсить номер
    try:
        post_number = int(text)
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Ошибка:</b> Введите корректный номер поста.\n\n"
            "Используйте /cancel для отмены.",
            parse_mode='HTML'
        )
        return ADMIN_POST_SELECTION_STATE
    
    # Валидировать номер
    total_posts = context.user_data.get('admin_total_posts', len(selector.messages))
    
    if post_number < 1 or post_number > total_posts:
        await update.message.reply_text(
            f"❌ <b>Ошибка:</b> Номер поста должен быть от 1 до {total_posts}.\n\n"
            "Используйте /cancel для отмены.",
            parse_mode='HTML'
        )
        return ADMIN_POST_SELECTION_STATE
    
    # Получить сообщение по индексу
    messages = selector.messages
    message = messages[post_number - 1]
    
    logger.info(f"Админ {user_id} выбрал пост #{post_number}: {message['title']}")
    
    # Сохранить выбранное сообщение в контексте
    context.user_data['admin_selected_message'] = message
    
    # Показать превью поста
    preview_text = f"📋 <b>Превью поста:</b>\n\n"
    preview_text += f"<b>Название:</b> {message['title']}\n\n"
    preview_text += f"<b>Текст:</b>\n{message['text'][:500]}"
    
    if len(message['text']) > 500:
        preview_text += "...\n\n(текст сокращен)"
    
    # Медиа информация
    photos = message.get('photos', [])
    videos = message.get('videos', [])
    
    if photos:
        preview_text += f"\n\n📸 <b>Фото:</b> {len(photos)} шт."
    if videos:
        preview_text += f"\n📹 <b>Видео:</b> {len(videos)} шт."
    
    # Кнопки для выбора куда отправить
    from config import CHANNEL_IDS
    keyboard = []
    
    # Кнопка "Во все каналы"
    keyboard.append([InlineKeyboardButton(
        f"📢 Отправить во все каналы ({len(CHANNEL_IDS)})",
        callback_data="admin_send_all_channels"
    )])
    
    # Кнопки для отдельных каналов
    for idx, channel_id in enumerate(CHANNEL_IDS, 1):
        keyboard.append([InlineKeyboardButton(
            f"📡 Канал {idx} (ID: {channel_id})",
            callback_data=f"admin_send_channel_{channel_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel_send")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        preview_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return ADMIN_CHANNEL_SELECTION_STATE


async def admin_send_to_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка поста в выбранные каналы."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    # Получить выбранное сообщение
    message = context.user_data.get('admin_selected_message')
    
    if not message:
        await query.message.edit_text(
            "❌ <b>Ошибка:</b> Сообщение не найдено.\n\n"
            "Используйте /start для возврата в меню.",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    # Определить каналы для отправки
    from config import CHANNEL_IDS
    
    if query.data == "admin_send_all_channels":
        target_channels = CHANNEL_IDS
        channel_desc = f"все каналы ({len(target_channels)})"
    elif query.data.startswith("admin_send_channel_"):
        channel_id = int(query.data.replace("admin_send_channel_", ""))
        target_channels = [channel_id]
        channel_desc = f"канал ID: {channel_id}"
    elif query.data == "admin_cancel_send":
        await query.message.edit_text(
            "❌ <b>Отправка отменена</b>\n\n"
            "Используйте /start для возврата в меню.",
            parse_mode='HTML'
        )
        # Очистить контекст
        context.user_data.pop('admin_selected_message', None)
        context.user_data.pop('admin_total_posts', None)
        return ConversationHandler.END
    else:
        await query.message.edit_text(
            "❌ <b>Ошибка:</b> Неизвестная команда.",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    logger.info(f"Админ {user_id} отправляет пост в {channel_desc}")
    
    # Показать сообщение "Отправка..."
    await query.message.edit_text(
        f"⏳ <b>Отправка поста...</b>\n\n"
        f"📝 {message['title']}\n"
        f"📡 Каналов: {channel_desc}\n\n"
        f"Пожалуйста, подождите...",
        parse_mode='HTML'
    )
    
    # Получить экземпляр бота
    bot_instance = context.bot_data.get('bot_instance')
    
    if not bot_instance:
        await query.message.edit_text(
            "❌ <b>Ошибка:</b> Не удалось получить доступ к боту.",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    # Отправить пост
    try:
        result = await bot_instance.send_specific_message(message, target_channels)
        
        success_count = result['success_count']
        error_count = result['error_count']
        total_channels = success_count + error_count
        
        # Формирование отчета
        if error_count == 0:
            status_emoji = "✅"
            status_text = "Пост успешно отправлен!"
        elif success_count == 0:
            status_emoji = "❌"
            status_text = "Не удалось отправить пост!"
        else:
            status_emoji = "⚠️"
            status_text = "Пост отправлен частично."
        
        report = (
            f"{status_emoji} <b>{status_text}</b>\n\n"
            f"📝 <b>Пост:</b> {message['title']}\n"
            f"📡 <b>Цель:</b> {channel_desc}\n"
            f"📊 <b>Статистика:</b>\n"
            f"  • Успешно: {success_count}/{total_channels}\n"
            f"  • Ошибок: {error_count}/{total_channels}\n\n"
            f"Используйте /start для возврата в меню."
        )
        
        await query.message.edit_text(report, parse_mode='HTML')
        
        logger.info(f"Админ-отправка завершена: успешно {success_count}, ошибок {error_count}")
        
    except Exception as e:
        logger.error(f"Ошибка при админ-отправке поста: {e}", exc_info=True)
        
        await query.message.edit_text(
            f"❌ <b>Ошибка при отправке поста!</b>\n\n"
            f"Подробности: {str(e)}\n\n"
            f"Используйте /start для возврата в меню.",
            parse_mode='HTML'
        )
    
    # Очистить контекст
    context.user_data.pop('admin_selected_message', None)
    context.user_data.pop('admin_total_posts', None)
    
    return ConversationHandler.END


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена админ-операции."""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} отменил админ-операцию")
    
    await update.message.reply_text(
        "❌ <b>Операция отменена</b>\n\n"
        "Используйте /start для возврата в главное меню.",
        parse_mode='HTML'
    )
    
    # Очистить контекст
    context.user_data.pop('admin_total_posts', None)
    context.user_data.pop('admin_selected_message', None)
    
    return ConversationHandler.END


# ConversationHandler для админ-панели
admin_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_send_post_button, pattern="^admin_send_post$")],
    states={
        ADMIN_PASSWORD_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_check_password)],
        ADMIN_POST_SELECTION_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_select_post)],
        ADMIN_CHANNEL_SELECTION_STATE: [
            CallbackQueryHandler(admin_send_to_channels, pattern="^admin_send_")
        ]
    },
    fallbacks=[CommandHandler("cancel", admin_cancel)],
    conversation_timeout=300,  # 5 минут
    per_message=False,
    per_chat=True,
    per_user=True
)


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
