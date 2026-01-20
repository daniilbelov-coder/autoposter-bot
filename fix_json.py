"""
Скрипт для исправления структуры messages_new.json
"""

import json
import re
from text_formatter import markdown_to_html


def fix_and_convert_messages():
    """Исправить структуру JSON и конвертировать в правильный формат."""
    
    # Прочитать файл как текст
    with open('messages_new.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Найти все объекты recurring_communications
    # Используем регулярное выражение для поиска всех массивов
    pattern = r'"recurring_communications":\s*\[(.*?)\]'
    matches = re.findall(pattern, content, re.DOTALL)
    
    # Альтернативный подход: читать по частям
    all_messages = []
    
    # Разделить файл на части по паттерну "recurring_communications"
    parts = content.split('"recurring_communications":')
    
    for i, part in enumerate(parts):
        if i == 0:  # Пропускаем первую часть (до первого recurring_communications)
            continue
        
        # Найти начало и конец массива
        bracket_count = 0
        start_idx = part.find('[')
        if start_idx == -1:
            continue
        
        end_idx = -1
        for j in range(start_idx, len(part)):
            if part[j] == '[':
                bracket_count += 1
            elif part[j] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = j
                    break
        
        if end_idx == -1:
            continue
        
        # Извлечь массив и попробовать распарсить
        array_str = part[start_idx:end_idx+1]
        try:
            messages = json.loads(array_str)
            all_messages.extend(messages)
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга части {i}: {e}")
            continue
    
    print(f"Найдено {len(all_messages)} сообщений")
    
    # Обработать каждое сообщение
    processed_messages = []
    for message in all_messages:
        processed = process_message(message)
        processed_messages.append(processed)
    
    # Сохранить в messages.json
    with open('messages.json', 'w', encoding='utf-8') as f:
        json.dump(processed_messages, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Конвертировано {len(processed_messages)} сообщений")
    print(f"✅ Файл messages.json обновлен")
    
    # Вывести статистику
    video_count = sum(1 for msg in processed_messages if 'videos' in msg and msg['videos'])
    photo_count = sum(1 for msg in processed_messages if 'photos' in msg and msg['photos'])
    print(f"📊 Сообщений с фото: {photo_count}")
    print(f"📊 Сообщений с видео: {video_count}")


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
    fix_and_convert_messages()
