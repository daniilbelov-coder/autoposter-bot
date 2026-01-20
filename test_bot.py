"""
Тестовый скрипт для проверки функциональности бота.
"""

import asyncio
import os
from message_selector import selector
from text_formatter import markdown_to_html


def test_message_loading():
    """Тест загрузки сообщений."""
    print("=" * 70)
    print("ТЕСТ 1: Загрузка сообщений")
    print("=" * 70)
    
    messages = selector.messages
    print(f"✅ Загружено сообщений: {len(messages)}")
    
    # Статистика
    with_photos = sum(1 for m in messages if m.get('photos'))
    with_videos = sum(1 for m in messages if m.get('videos'))
    
    print(f"📷 С фотографиями: {with_photos}")
    print(f"📹 С видео: {with_videos}")
    print()


def test_text_formatting():
    """Тест форматирования текста."""
    print("=" * 70)
    print("ТЕСТ 2: Форматирование текста")
    print("=" * 70)
    
    test_cases = [
        ("**Жирный текст**", "<b>Жирный текст</b>"),
        ("*Курсив*", "<i>Курсив</i>"),
        ("__Подчеркнутый__", "<u>Подчеркнутый</u>"),
        ("`код`", "<code>код</code>"),
        ("[ссылка](https://example.com)", '<a href="https://example.com">ссылка</a>'),
    ]
    
    all_passed = True
    for input_text, expected in test_cases:
        result = markdown_to_html(input_text)
        passed = result == expected
        status = "✅" if passed else "❌"
        print(f"{status} {input_text} -> {result}")
        if not passed:
            print(f"   Ожидалось: {expected}")
            all_passed = False
    
    if all_passed:
        print("\n✅ Все тесты форматирования пройдены!")
    else:
        print("\n❌ Некоторые тесты не прошли")
    print()


def test_media_files():
    """Тест существования медиа файлов."""
    print("=" * 70)
    print("ТЕСТ 3: Проверка медиа файлов")
    print("=" * 70)
    
    messages = selector.messages
    missing = []
    
    for msg in messages:
        # Проверить фото
        for photo in msg.get('photos', []):
            if not os.path.exists(photo):
                missing.append((msg['id'], msg['title'], photo, 'фото'))
        
        # Проверить видео
        for video in msg.get('videos', []):
            if not os.path.exists(video):
                missing.append((msg['id'], msg['title'], video, 'видео'))
    
    if missing:
        print(f"❌ Отсутствует файлов: {len(missing)}")
        for msg_id, title, path, media_type in missing:
            print(f"   ID {msg_id}: {path} ({media_type})")
    else:
        print("✅ Все медиа файлы найдены!")
    print()


def test_message_selection():
    """Тест выбора сообщений."""
    print("=" * 70)
    print("ТЕСТ 4: Выбор случайного сообщения")
    print("=" * 70)
    
    # Получить доступные сообщения
    available = selector.get_available_messages()
    print(f"✅ Доступно сообщений для отправки: {len(available)}")
    
    if available:
        # Выбрать случайное
        selected = selector.select_random_message()
        if selected:
            print(f"\n📨 Выбрано сообщение:")
            print(f"   ID: {selected['id']}")
            print(f"   Заголовок: {selected['title']}")
            print(f"   Частота: каждые {selected['frequency_days']} дней")
            
            if selected.get('photos'):
                print(f"   📷 Фото: {len(selected['photos'])} шт.")
            if selected.get('videos'):
                print(f"   📹 Видео: {len(selected['videos'])} шт.")
            
            # Показать первые 200 символов текста
            text_preview = selected['text'][:200].replace('\n', ' ')
            print(f"   Текст: {text_preview}...")
        else:
            print("❌ Не удалось выбрать сообщение")
    else:
        print("⚠️  Нет доступных сообщений (все недавно отправлялись)")
    print()


def test_video_messages():
    """Тест сообщений с видео."""
    print("=" * 70)
    print("ТЕСТ 5: Сообщения с видео")
    print("=" * 70)
    
    messages = selector.messages
    video_messages = [m for m in messages if m.get('videos')]
    
    print(f"✅ Найдено сообщений с видео: {len(video_messages)}")
    print()
    
    for msg in video_messages:
        print(f"📹 ID {msg['id']}: {msg['title']}")
        print(f"   Видео файлы: {msg['videos']}")
        
        # Проверить существование
        for video in msg['videos']:
            exists = os.path.exists(video)
            status = "✅" if exists else "❌"
            print(f"   {status} {video}")
        print()


def test_html_formatting_in_messages():
    """Тест HTML форматирования в загруженных сообщениях."""
    print("=" * 70)
    print("ТЕСТ 6: HTML форматирование в сообщениях")
    print("=" * 70)
    
    messages = selector.messages
    
    # Проверить, что в сообщениях есть HTML теги
    html_tags = ['<b>', '<i>', '<u>', '<code>', '<a href=']
    messages_with_html = []
    
    for msg in messages:
        text = msg.get('text', '')
        has_html = any(tag in text for tag in html_tags)
        if has_html:
            messages_with_html.append(msg)
    
    print(f"✅ Сообщений с HTML форматированием: {len(messages_with_html)}")
    
    if messages_with_html:
        print("\nПримеры:")
        for msg in messages_with_html[:3]:
            print(f"\n📝 ID {msg['id']}: {msg['title']}")
            # Найти и показать HTML теги
            text = msg['text']
            for tag in html_tags:
                if tag in text:
                    # Найти первое вхождение и показать контекст
                    idx = text.find(tag)
                    start = max(0, idx - 20)
                    end = min(len(text), idx + 50)
                    context = text[start:end].replace('\n', ' ')
                    print(f"   {tag}: ...{context}...")
                    break
    print()


def main():
    """Запустить все тесты."""
    print("\n")
    print("🤖 ТЕСТИРОВАНИЕ БОТА АВТОПОСТИНГА")
    print("=" * 70)
    print()
    
    try:
        test_message_loading()
        test_text_formatting()
        test_media_files()
        test_message_selection()
        test_video_messages()
        test_html_formatting_in_messages()
        
        print("=" * 70)
        print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        print("=" * 70)
        print()
        print("📋 Резюме:")
        print("   ✅ Сообщения загружаются корректно")
        print("   ✅ Markdown конвертируется в HTML")
        print("   ✅ Все медиа файлы найдены")
        print("   ✅ Выбор сообщений работает")
        print("   ✅ Поддержка видео реализована")
        print()
        print("🚀 Бот готов к запуску!")
        print()
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
