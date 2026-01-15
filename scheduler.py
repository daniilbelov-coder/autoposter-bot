"""
Модуль планировщика задач.
Настройка и управление расписанием отправки сообщений.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import POSTING_TIMES, TIMEZONE, logger


class BotScheduler:
    """Класс для управления планировщиком задач."""
    
    def __init__(self):
        """Инициализация планировщика."""
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        logger.info(f"Планировщик инициализирован с часовым поясом {TIMEZONE}")
    
    def add_posting_jobs(self, post_function):
        """
        Добавить задачи отправки сообщений по расписанию.
        
        Args:
            post_function: Асинхронная функция для отправки сообщений
        """
        for time_config in POSTING_TIMES:
            hour = time_config['hour']
            minute = time_config['minute']
            
            # Создать cron триггер
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone=TIMEZONE
            )
            
            # Добавить задачу
            self.scheduler.add_job(
                post_function,
                trigger=trigger,
                id=f'post_{hour:02d}_{minute:02d}',
                name=f'Отправка в {hour:02d}:{minute:02d}',
                replace_existing=True
            )
            
            logger.info(f"Добавлена задача отправки на {hour:02d}:{minute:02d} МСК")
    
    def start(self):
        """Запустить планировщик."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Планировщик запущен")
            
            # Вывести список запланированных задач
            jobs = self.scheduler.get_jobs()
            logger.info(f"Запланировано задач: {len(jobs)}")
            for job in jobs:
                logger.info(f"  - {job.name}: {job.next_run_time}")
        else:
            logger.warning("Планировщик уже запущен")
    
    def shutdown(self):
        """Остановить планировщик."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Планировщик остановлен")
        else:
            logger.warning("Планировщик не запущен")
    
    def get_jobs(self):
        """
        Получить список всех задач.
        
        Returns:
            Список задач
        """
        return self.scheduler.get_jobs()
    
    def remove_job(self, job_id: str):
        """
        Удалить задачу по ID.
        
        Args:
            job_id: ID задачи
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Задача {job_id} удалена")
        except Exception as e:
            logger.error(f"Ошибка при удалении задачи {job_id}: {e}")
    
    def pause(self):
        """Приостановить выполнение задач."""
        if self.scheduler.running:
            self.scheduler.pause()
            logger.info("Планировщик приостановлен")
    
    def resume(self):
        """Возобновить выполнение задач."""
        if self.scheduler.running:
            self.scheduler.resume()
            logger.info("Планировщик возобновлён")


# Создание глобального экземпляра планировщика
bot_scheduler = BotScheduler()
