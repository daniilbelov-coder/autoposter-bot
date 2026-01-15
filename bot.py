"""
Главный модуль бота для автоматической отправки сообщений в Telegram каналы
и обработки команд пользователей.
"""

import asyncio
import os
from typing import Optional, Dict, List
from telegram import Bot, InputMediaPhoto, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram.error import TelegramError
from config import BOT_TOKEN, CHANNEL_IDS, logger, MAX_PHOTOS_PER_POST
from database import db
from message_selector import selector
from scheduler import bot_scheduler
from handlers import start_command, help_command, status_command, button_callback, error_handler
from schedule_generator import generate_schedule_for_subscribers


class AutoPosterBot:
    """Класс для управления ботом автопостинга."""
    
    def __init__(self):
        """Инициализация бота."""
        self.bot = Bot(token=BOT_TOKEN)
        self.application = None
        logger.info("Бот инициализирован")
    
    async def send_message_to_channel(
        self, 
        channel_id: int, 
        message: Dict
    ) -> bool:
        """
        Отправить сообщение в один канал.
        
        Args:
            channel_id: ID канала
            message: Словарь с данными сообщения
            
        Returns:
            True, если отправка успешна
        """
        try:
            text = message['text']
            photos = message.get('photos', [])
            
            # Если нет фотографий - отправляем только текст
            if not photos:
                await self.bot.send_message(
                    chat_id=channel_id,
                    text=text,
                    parse_mode='HTML'
                )
                logger.info(f"Текстовое сообщение отправлено в канал {channel_id}")
                return True
            
            # Если одна фотография - отправляем send_photo
            if len(photos) == 1:
                photo_path = photos[0]
                
                if not os.path.exists(photo_path):
                    logger.error(f"Фото не найдено: {photo_path}")
                    return False
                
                with open(photo_path, 'rb') as photo_file:
                    await self.bot.send_photo(
                        chat_id=channel_id,
                        photo=photo_file,
                        caption=text,
                        parse_mode='HTML'
                    )
                
                logger.info(f"Сообщение с 1 фото отправлено в канал {channel_id}")
                return True
            
            # Если несколько фотографий - отправляем media group
            if len(photos) > MAX_PHOTOS_PER_POST:
                logger.warning(f"Слишком много фото ({len(photos)}), "
                             f"будут отправлены первые {MAX_PHOTOS_PER_POST}")
                photos = photos[:MAX_PHOTOS_PER_POST]
            
            media_group = []
            for idx, photo_path in enumerate(photos):
                if not os.path.exists(photo_path):
                    logger.error(f"Фото не найдено: {photo_path}")
                    continue
                
                with open(photo_path, 'rb') as photo_file:
                    # Добавляем caption только к первому фото
                    if idx == 0:
                        media_group.append(
                            InputMediaPhoto(
                                media=photo_file.read(),
                                caption=text,
                                parse_mode='HTML'
                            )
                        )
                    else:
                        media_group.append(
                            InputMediaPhoto(media=photo_file.read())
                        )
            
            if not media_group:
                logger.error("Не удалось загрузить ни одного фото")
                return False
            
            await self.bot.send_media_group(
                chat_id=channel_id,
                media=media_group
            )
            
            logger.info(f"Сообщение с {len(media_group)} фото отправлено в канал {channel_id}")
            return True
            
        except TelegramError as e:
            logger.error(f"Ошибка Telegram при отправке в канал {channel_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке в канал {channel_id}: {e}")
            return False
    
    async def post_message(self):
        """
        Основная функция отправки сообщения.
        Выбирает случайное доступное сообщение и отправляет его во все каналы.
        """
        logger.info("=" * 50)
        logger.info("Запуск процесса отправки сообщения")
        
        # Выбрать случайное сообщение
        message = selector.select_random_message()
        
        if not message:
            logger.warning("Нет доступных сообщений для отправки!")
            return
        
        message_id = message['id']
        message_title = message['title']
        
        logger.info(f"Отправка сообщения {message_id} ({message_title}) "
                   f"в {len(CHANNEL_IDS)} каналов")
        
        # Отправить во все каналы
        success_count = 0
        error_count = 0
        
        for channel_id in CHANNEL_IDS:
            logger.info(f"Отправка в канал {channel_id}...")
            
            success = await self.send_message_to_channel(channel_id, message)
            
            if success:
                success_count += 1
                db.log_message_sent(
                    message_id=message_id,
                    message_title=message_title,
                    channel_id=channel_id,
                    success=True
                )
            else:
                error_count += 1
                db.log_message_sent(
                    message_id=message_id,
                    message_title=message_title,
                    channel_id=channel_id,
                    success=False,
                    error_message="Ошибка отправки"
                )
            
            # Небольшая задержка между отправками в разные каналы
            await asyncio.sleep(1)
        
        logger.info(f"Отправка завершена: успешно {success_count}, ошибок {error_count}")
        logger.info("=" * 50)
    
    async def send_schedule_to_subscribers(self):
        """
        Отправить еженедельное расписание всем подписчикам.
        """
        logger.info("=" * 50)
        logger.info("Начало рассылки еженедельного расписания")
        
        # Получить список подписчиков
        subscribers = db.get_active_subscribers()
        
        if not subscribers:
            logger.info("Нет активных подписчиков")
            return
        
        logger.info(f"Найдено подписчиков: {len(subscribers)}")
        
        # Сгенерировать календарь
        try:
            schedule_file = generate_schedule_for_subscribers()
            logger.info(f"Календарь создан: {schedule_file}")
        except Exception as e:
            logger.error(f"Ошибка при генерации календаря: {e}", exc_info=True)
            return
        
        # Отправить каждому подписчику
        success_count = 0
        error_count = 0
        
        message_text = (
            "📅 <b>Календарь коммуникаций на неделю</b>\n\n"
            "Здравствуйте! Высылаем вам план публикаций на предстоящую неделю.\n\n"
            "В файле вы найдете:\n"
            "• Даты и время всех публикаций\n"
            "• Названия сообщений\n"
            "• Информацию о фотографиях\n\n"
            "📊 Хорошей недели!"
        )
        
        for subscriber in subscribers:
            user_id = subscriber['user_id']
            
            try:
                with open(schedule_file, 'rb') as file:
                    await self.bot.send_document(
                        chat_id=user_id,
                        document=file,
                        caption=message_text,
                        parse_mode='HTML',
                        filename=f"calendar_{os.path.basename(schedule_file)}"
                    )
                
                # Обновить время последней отправки
                db.update_last_sent_schedule(user_id)
                
                success_count += 1
                logger.info(f"Расписание отправлено пользователю {user_id}")
                
            except TelegramError as e:
                error_count += 1
                logger.error(f"Ошибка при отправке пользователю {user_id}: {e}")
            
            # Задержка между отправками
            await asyncio.sleep(0.5)
        
        logger.info(f"Рассылка завершена: успешно {success_count}, ошибок {error_count}")
        logger.info("=" * 50)
    
    async def test_send(self, message_id: Optional[int] = None):
        """
        Тестовая отправка сообщения (для проверки).
        
        Args:
            message_id: ID конкретного сообщения (если None - выбирается случайное)
        """
        logger.info("Запуск тестовой отправки")
        
        if message_id is not None:
            message = selector.get_message_by_id(message_id)
            if not message:
                logger.error(f"Сообщение с ID {message_id} не найдено")
                return
        else:
            message = selector.select_random_message()
            if not message:
                logger.error("Нет доступных сообщений")
                return
        
        logger.info(f"Тестовая отправка сообщения {message['id']} ({message['title']})")
        
        for channel_id in CHANNEL_IDS:
            await self.send_message_to_channel(channel_id, message)
            await asyncio.sleep(1)
    
    def setup_handlers(self):
        """Настроить обработчики команд и кнопок."""
        if self.application is None:
            self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавить обработчики команд
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("status", status_command))
        
        # Добавить обработчик кнопок
        self.application.add_handler(CallbackQueryHandler(button_callback))
        
        # Добавить обработчик ошибок
        self.application.add_error_handler(error_handler)
        
        logger.info("Обработчики команд настроены")
    
    def start(self):
        """Запустить бота с планировщиком."""
        logger.info("Запуск бота...")
        
        # Настроить обработчики команд
        self.setup_handlers()
        
        # Добавить задачи в планировщик
        bot_scheduler.add_posting_jobs(self.post_message)
        bot_scheduler.add_weekly_schedule_job(self.send_schedule_to_subscribers)
        
        # Запустить планировщик
        bot_scheduler.start()
        
        logger.info("Бот запущен и ожидает выполнения задач по расписанию")
        logger.info("Нажмите Ctrl+C для остановки")
        
        # Запустить обработчики команд
        self.application.run_polling()
    
    def stop(self):
        """Остановить бота."""
        logger.info("Остановка бота...")
        bot_scheduler.shutdown()
        if self.application:
            self.application.stop()
        logger.info("Бот остановлен")


async def main():
    """Главная функция для запуска бота."""
    # Создать экземпляр бота
    bot = AutoPosterBot()
    
    # Запустить бота
    bot.start()


if __name__ == '__main__':
    # Запуск бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа завершена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
