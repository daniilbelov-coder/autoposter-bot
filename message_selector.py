"""
Модуль для выбора сообщений на основе частоты и конфликтов.
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from config import MESSAGES_FILE, TIMEZONE, logger
from database import db
from text_formatter import format_message_text


class MessageSelector:
    """Класс для выбора подходящих сообщений для отправки."""
    
    def __init__(self, messages_file: str = MESSAGES_FILE):
        """
        Инициализация селектора сообщений.
        
        Args:
            messages_file: Путь к файлу с сообщениями
        """
        self.messages_file = messages_file
        self.messages = self.load_messages()
    
    def load_messages(self) -> List[Dict]:
        """
        Загрузить сообщения из JSON файла.
        
        Returns:
            Список сообщений
        """
        try:
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            
            # Форматировать текст сообщений (конвертация Markdown в HTML уже выполнена)
            # Но на всякий случай применяем форматирование
            formatted_messages = [format_message_text(msg) for msg in messages]
            
            logger.info(f"Загружено {len(formatted_messages)} сообщений из {self.messages_file}")
            return formatted_messages
        except FileNotFoundError:
            logger.error(f"Файл {self.messages_file} не найден!")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return []
    
    def is_message_available(self, message: Dict) -> bool:
        """
        Проверить, доступно ли сообщение для отправки по частоте.
        
        Args:
            message: Словарь с данными сообщения
            
        Returns:
            True, если сообщение можно отправить
        """
        message_id = message['id']
        frequency_days = message['frequency_days']
        
        # Получить дату последней отправки
        last_sent_date = db.get_last_sent_date(message_id)
        
        # Если сообщение ещё не отправлялось, оно доступно
        if last_sent_date is None:
            logger.info(f"Сообщение {message_id} ({message['title']}) ещё не отправлялось - доступно")
            return True
        
        # Проверить, прошло ли достаточно дней
        today = datetime.now(TIMEZONE).date()
        days_passed = (today - last_sent_date).days
        
        available = days_passed >= frequency_days
        
        if available:
            logger.info(f"Сообщение {message_id} ({message['title']}) доступно: "
                       f"прошло {days_passed} дней из {frequency_days} необходимых")
        else:
            logger.info(f"Сообщение {message_id} ({message['title']}) недоступно: "
                       f"прошло {days_passed} дней из {frequency_days} необходимых")
        
        return available
    
    def has_conflicts(self, message: Dict, today_sent_ids: List[int]) -> bool:
        """
        Проверить, есть ли конфликты с уже отправленными сегодня сообщениями.
        
        Args:
            message: Словарь с данными сообщения
            today_sent_ids: Список ID сообщений, отправленных сегодня
            
        Returns:
            True, если есть конфликт
        """
        conflict_ids = message.get('do_not_schedule_same_day_with', [])
        
        # Проверить пересечение
        conflicts = set(conflict_ids) & set(today_sent_ids)
        
        if conflicts:
            logger.info(f"Сообщение {message['id']} ({message['title']}) имеет конфликт "
                       f"с уже отправленными сегодня сообщениями: {conflicts}")
            return True
        
        return False
    
    def get_available_messages(self) -> List[Dict]:
        """
        Получить список всех доступных для отправки сообщений.
        
        Returns:
            Список доступных сообщений
        """
        # Получить список отправленных сегодня сообщений
        today_sent_ids = db.get_today_sent_messages()
        logger.info(f"Сегодня уже отправлено сообщений: {today_sent_ids}")
        
        available = []
        
        for message in self.messages:
            # Проверить частоту
            if not self.is_message_available(message):
                continue
            
            # Проверить конфликты
            if self.has_conflicts(message, today_sent_ids):
                continue
            
            available.append(message)
        
        logger.info(f"Найдено {len(available)} доступных сообщений")
        return available
    
    def select_random_message(self) -> Optional[Dict]:
        """
        Выбрать случайное сообщение из доступных.
        
        Returns:
            Словарь с данными сообщения или None, если нет доступных
        """
        available = self.get_available_messages()
        
        if not available:
            logger.warning("Нет доступных сообщений для отправки!")
            return None
        
        # Выбрать случайное сообщение
        selected = random.choice(available)
        logger.info(f"Выбрано сообщение {selected['id']} ({selected['title']})")
        
        return selected
    
    def get_message_by_id(self, message_id: int) -> Optional[Dict]:
        """
        Получить сообщение по ID.
        
        Args:
            message_id: ID сообщения
            
        Returns:
            Словарь с данными сообщения или None
        """
        for message in self.messages:
            if message['id'] == message_id:
                return message
        return None
    
    def reload_messages(self):
        """Перезагрузить сообщения из файла."""
        self.messages = self.load_messages()


# Создание глобального экземпляра селектора
selector = MessageSelector()
