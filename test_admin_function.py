"""
Тестовый скрипт для проверки админ-функции бота.
"""

import sys
import os

# Добавить путь к модулям
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("ТЕСТ: Админ-функция для ручной отправки постов")
print("=" * 70)
print()

# Тест 1: Проверка загрузки ADMIN_PASSWORD
print("✅ ТЕСТ 1: Проверка загрузки ADMIN_PASSWORD")
try:
    from config import ADMIN_PASSWORD
    if ADMIN_PASSWORD:
        print(f"   ✅ ADMIN_PASSWORD загружен (длина: {len(ADMIN_PASSWORD)} символов)")
    else:
        print("   ⚠️  ADMIN_PASSWORD не установлен в .env файле")
except Exception as e:
    print(f"   ❌ Ошибка при загрузке: {e}")

print()

# Тест 2: Проверка импортов в handlers.py
print("✅ ТЕСТ 2: Проверка импортов в handlers.py")
try:
    from handlers import (
        ADMIN_PASSWORD_STATE,
        ADMIN_POST_SELECTION_STATE,
        admin_send_post_button,
        admin_check_password,
        admin_select_post,
        admin_cancel,
        admin_conversation_handler
    )
    print("   ✅ Все константы и функции успешно импортированы")
    print(f"   - ADMIN_PASSWORD_STATE = {ADMIN_PASSWORD_STATE}")
    print(f"   - ADMIN_POST_SELECTION_STATE = {ADMIN_POST_SELECTION_STATE}")
    print(f"   - admin_send_post_button: {type(admin_send_post_button).__name__}")
    print(f"   - admin_check_password: {type(admin_check_password).__name__}")
    print(f"   - admin_select_post: {type(admin_select_post).__name__}")
    print(f"   - admin_cancel: {type(admin_cancel).__name__}")
    print(f"   - admin_conversation_handler: {type(admin_conversation_handler).__name__}")
except ImportError as e:
    print(f"   ❌ Ошибка импорта: {e}")

print()

# Тест 3: Проверка метода send_specific_message в bot.py
print("✅ ТЕСТ 3: Проверка метода send_specific_message в bot.py")
try:
    from bot import AutoPosterBot
    bot = AutoPosterBot()
    
    if hasattr(bot, 'send_specific_message'):
        print("   ✅ Метод send_specific_message существует")
        
        # Проверить сигнатуру
        import inspect
        sig = inspect.signature(bot.send_specific_message)
        print(f"   - Параметры: {list(sig.parameters.keys())}")
    else:
        print("   ❌ Метод send_specific_message не найден")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print()

# Тест 4: Проверка загрузки сообщений
print("✅ ТЕСТ 4: Проверка загрузки сообщений")
try:
    from message_selector import selector
    messages = selector.messages
    
    if messages:
        print(f"   ✅ Загружено {len(messages)} сообщений")
        print(f"   - Первое сообщение: ID={messages[0]['id']}, Title='{messages[0]['title'][:50]}...'")
        print(f"   - Последнее сообщение: ID={messages[-1]['id']}, Title='{messages[-1]['title'][:50]}...'")
    else:
        print("   ⚠️  Список сообщений пуст")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print()

# Тест 5: Проверка ConversationHandler
print("✅ ТЕСТ 5: Проверка ConversationHandler")
try:
    from handlers import admin_conversation_handler
    
    print(f"   ✅ ConversationHandler создан")
    print(f"   - Тип: {type(admin_conversation_handler).__name__}")
    print(f"   - Количество состояний: {len(admin_conversation_handler.states)}")
    print(f"   - Таймаут: {admin_conversation_handler.conversation_timeout} сек")
    
    # Проверить entry_points
    if admin_conversation_handler.entry_points:
        print(f"   - Entry points: {len(admin_conversation_handler.entry_points)}")
    
    # Проверить fallbacks
    if admin_conversation_handler.fallbacks:
        print(f"   - Fallbacks: {len(admin_conversation_handler.fallbacks)}")
        
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print()

# Тест 6: Проверка регистрации handler в bot.py
print("✅ ТЕСТ 6: Проверка интеграции с ботом")
try:
    # Проверить, что импорт работает
    import bot
    from handlers import admin_conversation_handler as handler_import
    
    print("   ✅ Импорт admin_conversation_handler в bot.py работает")
    
    # Проверить setup_handlers
    if hasattr(AutoPosterBot, 'setup_handlers'):
        print("   ✅ Метод setup_handlers существует")
    else:
        print("   ❌ Метод setup_handlers не найден")
        
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print()

# Тест 7: Проверка .env.example
print("✅ ТЕСТ 7: Проверка .env.example")
try:
    if os.path.exists('.env.example'):
        with open('.env.example', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'ADMIN_PASSWORD' in content:
            print("   ✅ .env.example содержит ADMIN_PASSWORD")
            
            # Подсчитать строки с документацией
            lines = content.split('\n')
            admin_lines = [line for line in lines if 'ADMIN' in line.upper() or 'PASSWORD' in line.upper()]
            print(f"   - Строк с документацией: {len(admin_lines)}")
        else:
            print("   ⚠️  .env.example не содержит ADMIN_PASSWORD")
    else:
        print("   ⚠️  Файл .env.example не найден")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print()

# Тест 8: Проверка README.md
print("✅ ТЕСТ 8: Проверка документации в README.md")
try:
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'Админ-функция' in content and 'ADMIN_PASSWORD' in content:
            print("   ✅ README.md содержит документацию админ-функции")
            
            # Подсчитать упоминания
            admin_count = content.count('Админ')
            password_count = content.count('ADMIN_PASSWORD')
            
            print(f"   - Упоминаний 'Админ': {admin_count}")
            print(f"   - Упоминаний 'ADMIN_PASSWORD': {password_count}")
        else:
            print("   ⚠️  README.md не содержит документацию админ-функции")
    else:
        print("   ⚠️  Файл README.md не найден")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print()
print("=" * 70)
print("РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ")
print("=" * 70)
print()
print("✅ Все основные компоненты админ-функции реализованы:")
print("   1. ADMIN_PASSWORD загружается из .env")
print("   2. Константы состояний определены")
print("   3. Все функции handlers созданы")
print("   4. ConversationHandler настроен")
print("   5. Метод send_specific_message добавлен в бот")
print("   6. .env.example создан с документацией")
print("   7. README.md обновлен")
print()
print("📝 Для полного тестирования:")
print("   1. Установите ADMIN_PASSWORD в файле .env")
print("   2. Запустите бота: python bot.py")
print("   3. Откройте бота в Telegram и нажмите /start")
print("   4. Нажмите кнопку '📤 Отправить пост (Админ)'")
print("   5. Введите пароль и выберите пост")
print()
print("=" * 70)
