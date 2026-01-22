"""
Главный модуль бота для автоматической отправки сообщений в Telegram каналы
и обработки команд пользователей.
"""

import asyncio
import os
from typing import Optional, Dict, List
from telegram import Bot, InputMediaPhoto, InputMediaVideo, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram.error import TelegramError
from config import BOT_TOKEN, CHANNEL_IDS, logger, MAX_PHOTOS_PER_POST
from database import db
from message_selector import selector
from scheduler import bot_scheduler
from handlers import (
    start_command, help_command, status_command, schedule_command, 
    button_callback, error_handler, admin_conversation_handler
)
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
            videos = message.get('videos', [])
            
            # Если нет медиа файлов - отправляем только текст
            if not photos and not videos:
                await self.bot.send_message(
                    chat_id=channel_id,
                    text=text,
                    parse_mode='HTML'
                )
                logger.info(f"Текстовое сообщение отправлено в канал {channel_id}")
                return True
            
            # Если есть только видео (без фото)
            if videos and not photos:
                # Если одно видео - отправляем send_video
                if len(videos) == 1:
                    video_path = videos[0]
                    
                    if not os.path.exists(video_path):
                        logger.error(f"Видео не найдено: {video_path}")
                        return False
                    
                    with open(video_path, 'rb') as video_file:
                        await self.bot.send_video(
                            chat_id=channel_id,
                            video=video_file,
                            caption=text,
                            parse_mode='HTML'
                        )
                    
                    logger.info(f"Сообщение с 1 видео отправлено в канал {channel_id}")
                    return True
                
                # Если несколько видео - отправляем media group
                media_group = []
                for idx, video_path in enumerate(videos):
                    if not os.path.exists(video_path):
                        logger.error(f"Видео не найдено: {video_path}")
                        continue
                    
                    with open(video_path, 'rb') as video_file:
                        # Добавляем caption только к первому видео
                        if idx == 0:
                            media_group.append(
                                InputMediaVideo(
                                    media=video_file.read(),
                                    caption=text,
                                    parse_mode='HTML'
                                )
                            )
                        else:
                            media_group.append(
                                InputMediaVideo(media=video_file.read())
                            )
                
                if not media_group:
                    logger.error("Не удалось загрузить ни одного видео")
                    return False
                
                await self.bot.send_media_group(
                    chat_id=channel_id,
                    media=media_group
                )
                
                logger.info(f"Сообщение с {len(media_group)} видео отправлено в канал {channel_id}")
                return True
            
            # Если одна фотография и нет видео - отправляем send_photo
            if len(photos) == 1 and not videos:
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
            
            # Если есть несколько медиа файлов (фото и/или видео) - отправляем media group
            all_media = photos + videos
            if len(all_media) > MAX_PHOTOS_PER_POST:
                logger.warning(f"Слишком много медиа ({len(all_media)}), "
                             f"будут отправлены первые {MAX_PHOTOS_PER_POST}")
                all_media = all_media[:MAX_PHOTOS_PER_POST]
            
            media_group = []
            for idx, media_path in enumerate(all_media):
                if not os.path.exists(media_path):
                    logger.error(f"Медиа файл не найден: {media_path}")
                    continue
                
                # Определить тип медиа по расширению
                is_video = media_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
                
                with open(media_path, 'rb') as media_file:
                    media_data = media_file.read()
                    
                    # Добавляем caption только к первому медиа
                    if idx == 0:
                        if is_video:
                            media_group.append(
                                InputMediaVideo(
                                    media=media_data,
                                    caption=text,
                                    parse_mode='HTML'
                                )
                            )
                        else:
                            media_group.append(
                                InputMediaPhoto(
                                    media=media_data,
                                    caption=text,
                                    parse_mode='HTML'
                                )
                            )
                    else:
                        if is_video:
                            media_group.append(InputMediaVideo(media=media_data))
                        else:
                            media_group.append(InputMediaPhoto(media=media_data))
            
            if not media_group:
                logger.error("Не удалось загрузить ни одного медиа файла")
                return False
            
            await self.bot.send_media_group(
                chat_id=channel_id,
                media=media_group
            )
            
            logger.info(f"Сообщение с {len(media_group)} медиа файлами отправлено в канал {channel_id}")
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
    
    async def send_specific_message(self, message: Dict) -> Dict:
        """
        Отправить конкретное сообщение во все каналы (для админа).
        
        Args:
            message: Словарь с данными сообщения
            
        Returns:
            Словарь с результатами: {'success_count': int, 'error_count': int, 'channels': list}
        """
        logger.info("=" * 50)
        logger.info(f"[АДМИН] Отправка сообщения {message['id']} ({message['title']})")
        
        message_id = message['id']
        message_title = message['title']
        
        success_count = 0
        error_count = 0
        channels_result = []
        
        for channel_id in CHANNEL_IDS:
            logger.info(f"[АДМИН] Отправка в канал {channel_id}...")
            
            success = await self.send_message_to_channel(channel_id, message)
            
            if success:
                success_count += 1
                channels_result.append({'channel_id': channel_id, 'success': True})
                db.log_message_sent(
                    message_id=message_id,
                    message_title=f"[АДМИН] {message_title}",
                    channel_id=channel_id,
                    success=True
                )
            else:
                error_count += 1
                channels_result.append({'channel_id': channel_id, 'success': False})
                db.log_message_sent(
                    message_id=message_id,
                    message_title=f"[АДМИН] {message_title}",
                    channel_id=channel_id,
                    success=False,
                    error_message="Ошибка отправки"
                )
            
            # Небольшая задержка между отправками
            await asyncio.sleep(1)
        
        logger.info(f"[АДМИН] Отправка завершена: успешно {success_count}, ошибок {error_count}")
        logger.info("=" * 50)
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'channels': channels_result
        }
    
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
        
        # Сохранить экземпляр бота в bot_data для доступа из handlers
        self.application.bot_data['bot_instance'] = self
        
        # Добавить обработчики команд
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("status", status_command))
        self.application.add_handler(CommandHandler("schedule", schedule_command))
        
        # Добавить админ conversation handler (должен быть перед CallbackQueryHandler)
        self.application.add_handler(admin_conversation_handler)
        
        # Добавить обработчик кнопок
        self.application.add_handler(CallbackQueryHandler(button_callback))
        
        # Добавить обработчик ошибок
        self.application.add_error_handler(error_handler)
        
        logger.info("Обработчики команд настроены")
    
    async def start_async(self):
        """Запустить бота асинхронно."""
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
        
        # Инициализировать и запустить polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # Держать бота запущенным
        try:
            # Бесконечный цикл для поддержания работы
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Получен сигнал остановки")
        finally:
            # Остановить бота
            await self.stop_async()
    
    async def stop_async(self):
        """Остановить бота асинхронно."""
        logger.info("Остановка бота...")
        bot_scheduler.shutdown()
        
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        
        logger.info("Бот остановлен")


if __name__ == '__main__':
    # Запуск бота
    try:
        bot = AutoPosterBot()
        asyncio.run(bot.start_async())
    except KeyboardInterrupt:
        logger.info("Программа завершена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
