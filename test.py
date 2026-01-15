"""
Скрипт для тестирования бота.
Позволяет отправить тестовое сообщение без ожидания расписания.
"""

import asyncio
from bot import AutoPosterBot


async def test_random_message():
    """Тестовая отправка случайного сообщения."""
    print("Запуск тестовой отправки случайного сообщения...")
    bot = AutoPosterBot()
    await bot.test_send()
    print("Тестовая отправка завершена!")


async def test_specific_message(message_id: int):
    """
    Тестовая отправка конкретного сообщения.
    
    Args:
        message_id: ID сообщения из messages.json
    """
    print(f"Запуск тестовой отправки сообщения ID {message_id}...")
    bot = AutoPosterBot()
    await bot.test_send(message_id=message_id)
    print("Тестовая отправка завершена!")


async def test_scheduled_post():
    """Тестовая отправка как при срабатывании расписания."""
    print("Запуск тестовой отправки по расписанию...")
    bot = AutoPosterBot()
    await bot.post_message()
    print("Тестовая отправка завершена!")


if __name__ == '__main__':
    print("Выберите режим тестирования:")
    print("1. Отправить случайное доступное сообщение")
    print("2. Отправить конкретное сообщение по ID")
    print("3. Тестовая отправка как по расписанию")
    
    choice = input("Введите номер (1-3): ").strip()
    
    if choice == '1':
        asyncio.run(test_random_message())
    elif choice == '2':
        msg_id = int(input("Введите ID сообщения: ").strip())
        asyncio.run(test_specific_message(msg_id))
    elif choice == '3':
        asyncio.run(test_scheduled_post())
    else:
        print("Неверный выбор!")
