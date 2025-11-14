import re
from datetime import datetime, timedelta
from typing import Dict, Optional

def extract_deadline_info(text: str) -> Optional[Dict]:
    """Извлечение информации о дедлайне из текста"""
    
    # Паттерны для дат
    date_patterns = [
        (r'(\d{1,2})[\.\/](\d{1,2})[\.\/](\d{2,4})', 'dd_mm_yyyy'),  # DD.MM.YYYY
        (r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)', 'russian_date'),
        (r'через\s+(\d+)\s+(день|дня|дней)', 'days_after'),
        (r'до\s+(\d{1,2})[\.\/](\d{1,2})', 'until_dd_mm'),
    ]
    
    # Поиск даты
    deadline_date = None
    for pattern, pattern_type in date_patterns:
        match = re.search(pattern, text.lower())
        if match:
            deadline_date = parse_date_from_match(match, pattern_type)
            if deadline_date:
                break
    
    if not deadline_date:
        return None
    
    # Извлечение названия (первые 3-7 слов)
    words = text.split()[:7]
    title = ' '.join(words)
    
    return {
        'title': title,
        'deadline': deadline_date,
        'subject': guess_subject(text),
        'confidence': 0.7
    }

def parse_date_from_match(match, pattern_type: str) -> Optional[datetime]:
    """Парсинг даты из найденного совпадения"""
    now = datetime.now()
    
    try:
        if pattern_type == 'days_after':
            days = int(match.group(1))
            return now + timedelta(days=days)
        
        elif pattern_type == 'russian_date':
            day = int(match.group(1))
            month_name = match.group(2)
            months = {
                'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
            }
            month = months[month_name]
            year = now.year if month >= now.month else now.year + 1
            return datetime(year, month, day)
        
        elif pattern_type in ['dd_mm_yyyy', 'until_dd_mm']:
            day, month, year = map(int, match.groups())
            if year < 100:
                year += 2000
            return datetime(year, month, day)
    
    except Exception:
        return None
    
    return None

def guess_subject(text: str) -> str:
    """Определение предмета по ключевым словам"""
    subject_keywords = {
        'математика': ['мат', 'алгебр', 'геометр', 'математик'],
        'программирование': ['прог', 'код', 'алгоритм', 'python', 'java'],
        'физика': ['физик', 'механи', 'оптик', 'термодинамик'],
        'английский': ['англ', 'english', 'language', 'speaking']
    }
    
    text_lower = text.lower()
    for subject, keywords in subject_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return subject
    
    return 'другое'