"""
Модуль конфигурации бота.
Загружает настройки из .env файла и определяет константы.
"""

import os
from dotenv import load_dotenv
import pytz

# Загрузка переменных окружения из .env файла
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# ID каналов для отправки сообщений (список)
CHANNEL_IDS_STR = os.getenv('CHANNEL_IDS', '')
if not CHANNEL_IDS_STR:
    raise ValueError("CHANNEL_IDS не найден в .env файле!")

# Парсинг списка каналов
CHANNEL_IDS = [int(channel_id.strip()) for channel_id in CHANNEL_IDS_STR.split(',') if channel_id.strip()]

if not CHANNEL_IDS:
    raise ValueError("CHANNEL_IDS пуст или неправильно отформатирован!")

# Часовой пояс
TIMEZONE_STR = os.getenv('TIMEZONE', 'Europe/Moscow')
TIMEZONE = pytz.timezone(TIMEZONE_STR)

# Путь к базе данных
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot_data.db')

# Время отправки сообщений (часы и минуты в формате МСК)
POSTING_TIMES = [
    {'hour': 11, 'minute': 0},
    {'hour': 13, 'minute': 0},
    {'hour': 16, 'minute': 0},
]

# Путь к файлу с сообщениями
MESSAGES_FILE = 'messages.json'

# Максимальное количество фотографий в одном media group
MAX_PHOTOS_PER_POST = 10

# Админ пароль для ручной отправки постов
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    import logging
    logging.warning("ADMIN_PASSWORD не установлен в .env файле! Админ-функции будут недоступны.")

# Логирование
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
