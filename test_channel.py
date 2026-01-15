"""
Скрипт для тестирования подключения бота к каналу.
Помогает проверить ID канала и права бота.
"""

import asyncio
import sys
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')


async def test_channel(channel_id: int):
    """
    Протестировать подключение к каналу.
    
    Args:
        channel_id: ID канала (например: -1001234567890)
    """
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        print("❌ Ошибка: BOT_TOKEN не настроен в .env файле!")
        print("Откройте .env и добавьте ваш токен от @BotFather")
        return
    
    print("=" * 60)
    print("🤖 ТЕСТ ПОДКЛЮЧЕНИЯ БОТА К КАНАЛУ")
    print("=" * 60)
    print(f"\n📋 Токен бота: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"📺 ID канала: {channel_id}")
    print("\n⏳ Пытаюсь подключиться...\n")
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Получить информацию о боте
        bot_info = await bot.get_me()
        print(f"✅ Бот подключен: @{bot_info.username}")
        print(f"   Имя: {bot_info.first_name}")
        print(f"   ID: {bot_info.id}\n")
        
        # Получить информацию о канале
        print("⏳ Получаю информацию о канале...")
        try:
            chat = await bot.get_chat(chat_id=channel_id)
            print(f"✅ Канал найден!")
            print(f"   Название: {chat.title}")
            print(f"   Тип: {chat.type}")
            print(f"   ID: {chat.id}\n")
        except TelegramError as e:
            print(f"❌ Не удалось получить информацию о канале: {e}")
            print("   Возможные причины:")
            print("   - Неправильный ID канала")
            print("   - Бот не добавлен в канал\n")
            return
        
        # Проверить права администратора
        print("⏳ Проверяю права бота...")
        try:
            admins = await bot.get_chat_administrators(chat_id=channel_id)
            bot_is_admin = False
            bot_permissions = None
            
            for admin in admins:
                if admin.user.id == bot_info.id:
                    bot_is_admin = True
                    bot_permissions = admin
                    break
            
            if bot_is_admin:
                print("✅ Бот является администратором канала!")
                if hasattr(bot_permissions, 'can_post_messages'):
                    if bot_permissions.can_post_messages:
                        print("✅ Право 'Публикация сообщений': есть\n")
                    else:
                        print("⚠️  Право 'Публикация сообщений': НЕТ!")
                        print("   Дайте боту право публиковать сообщения!\n")
                        return
            else:
                print("❌ Бот НЕ является администратором!")
                print("   Добавьте бота в администраторы канала\n")
                return
                
        except TelegramError as e:
            print(f"⚠️  Не удалось проверить права: {e}\n")
        
        # Отправить тестовое сообщение
        print("⏳ Отправляю тестовое сообщение...")
        test_message = await bot.send_message(
            chat_id=channel_id,
            text="✅ Тест успешен!\n\n🤖 Бот подключен и готов к работе.\n"
                 "Это тестовое сообщение можно удалить."
        )
        print(f"✅ Сообщение отправлено! (ID: {test_message.message_id})")
        
        print("\n" + "=" * 60)
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("=" * 60)
        print("\n✅ Используйте этот ID в .env файле:")
        print(f"   CHANNEL_IDS={channel_id}")
        print("\n✅ Бот готов к работе!")
        
    except TelegramError as e:
        print(f"\n❌ ОШИБКА TELEGRAM: {e}")
        print("\n📝 Возможные решения:")
        print("1. Проверьте токен бота (BOT_TOKEN в .env)")
        print("2. Убедитесь, что ID канала правильный (начинается с -100)")
        print("3. Добавьте бота в канал как администратора")
        print("4. Дайте боту право 'Публикация сообщений'")
        
    except Exception as e:
        print(f"\n❌ НЕОЖИДАННАЯ ОШИБКА: {e}")


async def find_channel_id():
    """Помощник для получения ID канала."""
    print("=" * 60)
    print("📍 КАК ПОЛУЧИТЬ ID КАНАЛА")
    print("=" * 60)
    print("\n1️⃣  Способ 1: Через @userinfobot (рекомендуется)")
    print("   • Перешлите любое сообщение из канала боту @userinfobot")
    print("   • Скопируйте ID (начинается с -100)")
    print("\n2️⃣  Способ 2: Через @getmyid_bot")
    print("   • Добавьте @getmyid_bot в ваш канал")
    print("   • Бот автоматически отправит ID")
    print("\n3️⃣  Способ 3: Через веб-версию Telegram")
    print("   • Откройте канал на https://web.telegram.org/")
    print("   • Посмотрите ID в URL после символа #")
    print("\n" + "=" * 60)


async def main():
    """Главная функция."""
    print("\n")
    
    if len(sys.argv) > 1:
        # ID канала передан как аргумент
        try:
            channel_id = int(sys.argv[1])
            await test_channel(channel_id)
        except ValueError:
            print("❌ Ошибка: ID канала должен быть числом!")
            print("Пример: python test_channel.py -1001234567890")
    else:
        # Интерактивный режим
        await find_channel_id()
        print("\n")
        
        # Попробовать загрузить из .env
        load_dotenv()
        channel_ids_str = os.getenv('CHANNEL_IDS', '')
        
        if channel_ids_str and channel_ids_str != '-1001234567890':
            channel_ids = [int(ch.strip()) for ch in channel_ids_str.split(',') if ch.strip()]
            if channel_ids:
                print(f"📋 Найдены каналы в .env: {channel_ids}")
                print("\n")
                for channel_id in channel_ids:
                    await test_channel(channel_id)
                    print("\n")
                return
        
        # Запросить ID у пользователя
        try:
            channel_id_input = input("Введите ID канала (например: -1001234567890): ").strip()
            channel_id = int(channel_id_input)
            await test_channel(channel_id)
        except ValueError:
            print("❌ Ошибка: ID канала должен быть числом!")
        except KeyboardInterrupt:
            print("\n\n👋 Отменено пользователем")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Программа прервана")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
