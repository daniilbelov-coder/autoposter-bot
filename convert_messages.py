"""
Скрипт для конвертации messages_new.json в правильный формат.
"""

import json
import os
from text_formatter import markdown_to_html


def convert_messages():
    """Конвертировать messages_new.json в правильный формат."""
    
    # Загрузить messages_new.json
    with open('messages_new.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Извлечь все сообщения из всех recurring_communications массивов
    all_messages = []
    
    # Проверить структуру
    if isinstance(data, dict) and 'recurring_communications' in data:
        messages_list = data['recurring_communications']
    elif isinstance(data, list):
        messages_list = data
    else:
        print("Неожиданная структура данных")
        return
    
    # Обработать каждое сообщение
    for message in messages_list:
        # Пропустить вложенные объекты с recurring_communications
        if isinstance(message, dict):
            if 'recurring_communications' in message:
                # Это вложенный объект, берем сообщения из него
                for nested_msg in message['recurring_communications']:
                    processed_msg = process_message(nested_msg)
                    all_messages.append(processed_msg)
            else:
                # Это обычное сообщение
                processed_msg = process_message(message)
                all_messages.append(processed_msg)
    
    # Сохранить в messages.json
    with open('messages.json', 'w', encoding='utf-8') as f:
        json.dump(all_messages, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Конвертировано {len(all_messages)} сообщений")
    print(f"✅ Файл messages.json обновлен")


def process_message(message):
    """
    Обработать одно сообщение:
    - Конвертировать markdown в HTML
    - Добавить префикс photos/ к путям
    - Определить тип медиа (фото/видео)
    """
    processed = message.copy()
    
    # Конвертировать markdown в HTML
    if 'text' in processed:
        processed['text'] = markdown_to_html(processed['text'])
    
    # Обработать пути к медиа файлам
    if 'photos' in processed and processed['photos']:
        media_files = []
        video_files = []
        
        for photo in processed['photos']:
            # Добавить префикс photos/ если его нет
            if not photo.startswith('photos/'):
                full_path = f'photos/{photo}'
            else:
                full_path = photo
            
            # Определить, это фото или видео
            if photo.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                video_files.append(full_path)
            else:
                media_files.append(full_path)
        
        # Обновить поля
        processed['photos'] = media_files
        
        # Если есть видео, добавить отдельное поле
        if video_files:
            processed['videos'] = video_files
    
    return processed


if __name__ == '__main__':
    convert_messages()
