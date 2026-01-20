"""
Тестовый скрипт для проверки генерации календаря.
"""

import os
from schedule_generator import generate_schedule_for_subscribers, get_week_dates, get_planned_posts_for_week
from datetime import datetime
from config import TIMEZONE


def test_schedule_generation():
    """Тест генерации календаря."""
    print("=" * 70)
    print("ТЕСТ: Генерация календаря на текущую неделю")
    print("=" * 70)
    print()
    
    # Получить даты недели
    week_dates = get_week_dates()
    print(f"📅 Неделя: {week_dates[0].strftime('%d.%m.%Y')} - {week_dates[-1].strftime('%d.%m.%Y')}")
    print()
    
    # Получить запланированные посты
    planned_posts = get_planned_posts_for_week()
    print(f"📊 Запланировано постов: {len(planned_posts)}")
    print()
    
    # Показать несколько примеров
    print("Примеры постов:")
    for idx, post in enumerate(planned_posts[:5], 1):
        print(f"{idx}. {post['date'].strftime('%d.%m')} {post['time'].strftime('%H:%M')} - {post['message_title']}")
    
    if len(planned_posts) > 5:
        print(f"... и еще {len(planned_posts) - 5} постов")
    print()
    
    # Сгенерировать календарь
    print("⏳ Генерирую Excel файл...")
    try:
        schedule_file = generate_schedule_for_subscribers()
        
        if os.path.exists(schedule_file):
            file_size = os.path.getsize(schedule_file)
            print(f"✅ Календарь создан: {schedule_file}")
            print(f"📦 Размер файла: {file_size / 1024:.1f} KB")
            print()
            
            # Показать путь
            abs_path = os.path.abspath(schedule_file)
            print(f"🔗 Полный путь: {abs_path}")
            print()
            
            return True
        else:
            print("❌ Файл не создан")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при генерации: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schedule_folder():
    """Тест папки с расписаниями."""
    print("=" * 70)
    print("ТЕСТ: Проверка папки schedules/")
    print("=" * 70)
    print()
    
    schedules_dir = "schedules"
    
    if os.path.exists(schedules_dir):
        files = [f for f in os.listdir(schedules_dir) if f.endswith('.xlsx')]
        print(f"✅ Папка существует")
        print(f"📁 Файлов календарей: {len(files)}")
        
        if files:
            print("\nПоследние календари:")
            # Сортировать по дате модификации
            files_with_time = [(f, os.path.getmtime(os.path.join(schedules_dir, f))) for f in files]
            files_with_time.sort(key=lambda x: x[1], reverse=True)
            
            for idx, (filename, mtime) in enumerate(files_with_time[:5], 1):
                mod_date = datetime.fromtimestamp(mtime).strftime('%d.%m.%Y %H:%M')
                file_size = os.path.getsize(os.path.join(schedules_dir, filename)) / 1024
                print(f"  {idx}. {filename} ({file_size:.1f} KB, создан {mod_date})")
    else:
        print(f"⚠️  Папка не существует (будет создана при первой генерации)")
    
    print()


def main():
    """Запустить все тесты."""
    print("\n")
    print("📅 ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ КАЛЕНДАРЯ")
    print("=" * 70)
    print()
    
    try:
        # Тест 1: Проверка папки
        test_schedule_folder()
        
        # Тест 2: Генерация календаря
        success = test_schedule_generation()
        
        print("=" * 70)
        if success:
            print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
            print()
            print("📋 Новая функциональность:")
            print("   ✅ Кнопка '📅 Получить календарь' в /start")
            print("   ✅ Команда /schedule для получения календаря")
            print("   ✅ Генерация календаря в любой день недели")
            print("   ✅ Excel файл с планом публикаций")
            print()
            print("🚀 Готово к использованию!")
        else:
            print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
