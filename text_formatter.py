"""
Модуль для форматирования текста сообщений.
Конвертирует Markdown форматирование в HTML для Telegram.
"""

import re


def markdown_to_html(text: str) -> str:
    """
    Конвертировать Markdown форматирование в HTML.
    
    Поддерживаемые форматы:
    - **текст** -> <b>текст</b> (жирный)
    - *текст* -> <i>текст</i> (курсив)
    - __текст__ -> <u>текст</u> (подчеркнутый)
    - `текст` -> <code>текст</code> (моноширинный)
    
    Args:
        text: Текст с Markdown форматированием
        
    Returns:
        Текст с HTML форматированием
    """
    if not text:
        return text
    
    # Жирный текст: **текст** -> <b>текст</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    
    # Курсив: *текст* (но не если это часть эмодзи или после **)
    # Используем negative lookbehind и lookahead чтобы избежать конфликтов
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    
    # Подчеркнутый: __текст__ -> <u>текст</u>
    text = re.sub(r'__(.+?)__', r'<u>\1</u>', text)
    
    # Моноширинный: `текст` -> <code>текст</code>
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    
    # Ссылки: [текст](url) -> <a href="url">текст</a>
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    
    return text


def format_message_text(message: dict) -> dict:
    """
    Форматировать текст сообщения, конвертируя Markdown в HTML.
    
    Args:
        message: Словарь с данными сообщения
        
    Returns:
        Обновленный словарь сообщения
    """
    if 'text' in message and message['text']:
        message['text'] = markdown_to_html(message['text'])
    
    return message
