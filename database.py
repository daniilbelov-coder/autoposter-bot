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
        """Создание таблиц, если их нет."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица истории отправок в каналы
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
            
            # Таблица подписчиков на еженедельное расписание
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscribers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    subscribed_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    last_sent_schedule TIMESTAMP
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
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON subscribers(user_id)
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
    
    # --- Методы для работы с подписчиками ---
    
    def add_subscriber(self, user_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None) -> bool:
        """
        Добавить подписчика.
        
        Args:
            user_id: Telegram ID пользователя
            username: Username пользователя
            first_name: Имя
            last_name: Фамилия
            
        Returns:
            True, если добавлен успешно
        """
        now = datetime.now(TIMEZONE)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO subscribers 
                    (user_id, username, first_name, last_name, subscribed_at, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (user_id, username, first_name, last_name, 
                      now.strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
                logger.info(f"Подписчик добавлен: {user_id} (@{username})")
                return True
            except sqlite3.IntegrityError:
                # Пользователь уже подписан, активируем подписку
                cursor.execute('''
                    UPDATE subscribers 
                    SET is_active = 1, username = ?, first_name = ?, last_name = ?
                    WHERE user_id = ?
                ''', (username, first_name, last_name, user_id))
                conn.commit()
                logger.info(f"Подписка активирована для: {user_id}")
                return True
    
    def remove_subscriber(self, user_id: int) -> bool:
        """
        Отписать пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True, если отписан успешно
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE subscribers 
                SET is_active = 0
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Подписчик отписан: {user_id}")
                return True
            return False
    
    def is_subscribed(self, user_id: int) -> bool:
        """
        Проверить, подписан ли пользователь.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True, если подписан
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT is_active 
                FROM subscribers 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            return result and result[0] == 1
    
    def get_active_subscribers(self) -> List[dict]:
        """
        Получить список активных подписчиков.
        
        Returns:
            Список словарей с данными подписчиков
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, subscribed_at
                FROM subscribers 
                WHERE is_active = 1
                ORDER BY subscribed_at DESC
            ''')
            
            subscribers = []
            for row in cursor.fetchall():
                subscribers.append({
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'subscribed_at': row[4]
                })
            
            return subscribers
    
    def update_last_sent_schedule(self, user_id: int):
        """
        Обновить время последней отправки расписания.
        
        Args:
            user_id: Telegram ID пользователя
        """
        now = datetime.now(TIMEZONE)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE subscribers 
                SET last_sent_schedule = ?
                WHERE user_id = ?
            ''', (now.strftime('%Y-%m-%d %H:%M:%S'), user_id))
            conn.commit()
    
    def get_subscribers_count(self) -> int:
        """
        Получить количество активных подписчиков.
        
        Returns:
            Количество подписчиков
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) 
                FROM subscribers 
                WHERE is_active = 1
            ''')
            return cursor.fetchone()[0]


# Создание глобального экземпляра базы данных
db = Database()
