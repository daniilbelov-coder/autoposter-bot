"""
Скрипт для просмотра статистики отправленных сообщений.
"""

import sqlite3
from datetime import datetime
from config import DATABASE_PATH
from message_selector import selector


def print_separator():
    """Печать разделителя."""
    print("=" * 80)


def show_all_statistics():
    """Показать статистику по всем сообщениям."""
    print_separator()
    print("СТАТИСТИКА ОТПРАВОК ПО ВСЕМ СООБЩЕНИЯМ")
    print_separator()
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM message_history WHERE success = 1")
        total_success = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message_history WHERE success = 0")
        total_errors = cursor.fetchone()[0]
        
        print(f"\nОбщая статистика:")
        print(f"  Успешных отправок: {total_success}")
        print(f"  Ошибок: {total_errors}")
        print(f"  Всего попыток: {total_success + total_errors}")
        
        # Статистика по каждому сообщению
        print("\nСтатистика по сообщениям:")
        print(f"{'ID':<5} {'Название':<30} {'Отправок':<12} {'Последняя отправка':<20}")
        print("-" * 80)
        
        cursor.execute("""
            SELECT 
                message_id,
                message_title,
                COUNT(*) as count,
                MAX(sent_date) as last_sent
            FROM message_history
            WHERE success = 1
            GROUP BY message_id, message_title
            ORDER BY message_id
        """)
        
        for row in cursor.fetchall():
            msg_id, title, count, last_sent = row
            title_short = title[:28] + '..' if len(title) > 30 else title
            print(f"{msg_id:<5} {title_short:<30} {count:<12} {last_sent or 'Никогда':<20}")


def show_recent_posts(limit=10):
    """
    Показать последние отправки.
    
    Args:
        limit: Количество записей
    """
    print_separator()
    print(f"ПОСЛЕДНИЕ {limit} ОТПРАВОК")
    print_separator()
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                sent_datetime,
                message_id,
                message_title,
                channel_id,
                success,
                error_message
            FROM message_history
            ORDER BY sent_datetime DESC
            LIMIT ?
        """, (limit,))
        
        print(f"\n{'Дата и время':<20} {'ID':<5} {'Название':<25} {'Канал':<15} {'Статус':<10}")
        print("-" * 80)
        
        for row in cursor.fetchall():
            dt, msg_id, title, channel, success, error = row
            title_short = title[:23] + '..' if len(title) > 25 else title
            status = "✓ Успех" if success else "✗ Ошибка"
            print(f"{dt:<20} {msg_id:<5} {title_short:<25} {channel:<15} {status:<10}")
            if error:
                print(f"  └─ Ошибка: {error}")


def show_today_posts():
    """Показать отправки за сегодня."""
    print_separator()
    print("ОТПРАВКИ ЗА СЕГОДНЯ")
    print_separator()
    
    today = datetime.now().date().strftime('%Y-%m-%d')
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                sent_datetime,
                message_id,
                message_title,
                channel_id,
                success
            FROM message_history
            WHERE sent_date = ?
            ORDER BY sent_datetime DESC
        """, (today,))
        
        rows = cursor.fetchall()
        
        if not rows:
            print("\nСегодня ещё не было отправок.")
            return
        
        print(f"\nВсего отправок сегодня: {len(rows)}")
        print(f"\n{'Время':<10} {'ID':<5} {'Название':<30} {'Канал':<15} {'Статус':<10}")
        print("-" * 80)
        
        for row in rows:
            dt, msg_id, title, channel, success = row
            time = dt.split()[1][:5]  # Только время HH:MM
            title_short = title[:28] + '..' if len(title) > 30 else title
            status = "✓ Успех" if success else "✗ Ошибка"
            print(f"{time:<10} {msg_id:<5} {title_short:<30} {channel:<15} {status:<10}")


def show_available_messages():
    """Показать доступные для отправки сообщения."""
    print_separator()
    print("ДОСТУПНЫЕ ДЛЯ ОТПРАВКИ СООБЩЕНИЯ")
    print_separator()
    
    available = selector.get_available_messages()
    
    if not available:
        print("\nНет доступных сообщений для отправки!")
        return
    
    print(f"\nВсего доступных сообщений: {len(available)}")
    print(f"\n{'ID':<5} {'Название':<35} {'Частота':<15}")
    print("-" * 80)
    
    for msg in available:
        msg_id = msg['id']
        title = msg['title']
        freq = f"{msg['frequency_days']} дней"
        title_short = title[:33] + '..' if len(title) > 35 else title
        print(f"{msg_id:<5} {title_short:<35} {freq:<15}")


def main():
    """Главная функция."""
    while True:
        print("\n" + "=" * 80)
        print("СТАТИСТИКА AUTOPOSTER BOT")
        print("=" * 80)
        print("\nВыберите действие:")
        print("1. Общая статистика по всем сообщениям")
        print("2. Последние 10 отправок")
        print("3. Отправки за сегодня")
        print("4. Доступные для отправки сообщения")
        print("5. Выход")
        
        choice = input("\nВведите номер (1-5): ").strip()
        
        if choice == '1':
            show_all_statistics()
        elif choice == '2':
            show_recent_posts(10)
        elif choice == '3':
            show_today_posts()
        elif choice == '4':
            show_available_messages()
        elif choice == '5':
            print("\nДо свидания!")
            break
        else:
            print("\n❌ Неверный выбор!")
        
        input("\nНажмите Enter для продолжения...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем.")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
