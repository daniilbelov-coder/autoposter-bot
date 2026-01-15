"""
Модуль для работы с базой данных SQLite.
Хранит историю отправленных сообщений.
"""

import sqlite3
from datetime import datetime, date
from typing import List, Optional
from config import DATABASE_PATH, TIMEZONE, logger


class Database:
    """Класс для работы с базой данных."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Инициализация подключения к базе данных.
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Создание таблицы message_history, если её нет."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    message_title TEXT NOT NULL,
                    sent_date DATE NOT NULL,
                    sent_datetime TIMESTAMP NOT NULL,
                    channel_id INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT
                )
            ''')
            
            # Создание индексов для ускорения запросов
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_id 
                ON message_history(message_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sent_date 
                ON message_history(sent_date)
            ''')
            
            conn.commit()
            logger.info("База данных инициализирована")
    
    def get_last_sent_date(self, message_id: int) -> Optional[date]:
        """
        Получить дату последней успешной отправки сообщения.
        
        Args:
            message_id: ID сообщения
            
        Returns:
            Дата последней отправки или None, если сообщение ещё не отправлялось
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(sent_date) 
                FROM message_history 
                WHERE message_id = ? AND success = 1
            ''', (message_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                return datetime.strptime(result[0], '%Y-%m-%d').date()
            return None
    
    def get_today_sent_messages(self) -> List[int]:
        """
        Получить список ID сообщений, отправленных сегодня.
        
        Returns:
            Список ID сообщений
        """
        today = datetime.now(TIMEZONE).date()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT message_id 
                FROM message_history 
                WHERE sent_date = ? AND success = 1
            ''', (today.strftime('%Y-%m-%d'),))
            
            return [row[0] for row in cursor.fetchall()]
    
    def log_message_sent(
        self, 
        message_id: int, 
        message_title: str,
        channel_id: int,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Записать лог отправки сообщения.
        
        Args:
            message_id: ID сообщения
            message_title: Заголовок сообщения
            channel_id: ID канала
            success: Успешность отправки
            error_message: Сообщение об ошибке (если есть)
        """
        now = datetime.now(TIMEZONE)
        today = now.date()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO message_history 
                (message_id, message_title, sent_date, sent_datetime, channel_id, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id,
                message_title,
                today.strftime('%Y-%m-%d'),
                now.strftime('%Y-%m-%d %H:%M:%S'),
                channel_id,
                success,
                error_message
            ))
            conn.commit()
            
            status = "успешно" if success else "с ошибкой"
            logger.info(f"Лог отправки: сообщение {message_id} ({message_title}) "
                       f"в канал {channel_id} - {status}")
    
    def get_message_statistics(self, message_id: int) -> dict:
        """
        Получить статистику отправок для сообщения.
        
        Args:
            message_id: ID сообщения
            
        Returns:
            Словарь со статистикой
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Общее количество отправок
            cursor.execute('''
                SELECT COUNT(*) 
                FROM message_history 
                WHERE message_id = ? AND success = 1
            ''', (message_id,))
            total_sent = cursor.fetchone()[0]
            
            # Дата последней отправки
            cursor.execute('''
                SELECT MAX(sent_date) 
                FROM message_history 
                WHERE message_id = ? AND success = 1
            ''', (message_id,))
            last_sent = cursor.fetchone()[0]
            
            # Количество ошибок
            cursor.execute('''
                SELECT COUNT(*) 
                FROM message_history 
                WHERE message_id = ? AND success = 0
            ''', (message_id,))
            errors = cursor.fetchone()[0]
            
            return {
                'total_sent': total_sent,
                'last_sent': last_sent,
                'errors': errors
            }
    
    def close(self):
        """Закрытие соединения с базой данных (для совместимости)."""
        # SQLite не требует явного закрытия при использовании context manager
        pass


# Создание глобального экземпляра базы данных
db = Database()
