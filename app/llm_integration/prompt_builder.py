# Код для формирования промптов для LLM 

import logging
import os
import json
import datetime

from .constants import DETAILED_EXTRACTION_PROMPT

def load_mapping_file(file_path: str) -> str:
    """Загружает содержимое файла справочника.

    Args:
        file_path: Путь к файлу справочника.

    Returns:
        Содержимое файла в виде строки.

    Raises:
        FileNotFoundError: Если файл не найден по указанному пути.
        IOError: Если произошла ошибка при чтении файла.
    """
    if not os.path.exists(file_path):
        logging.error(f"Файл справочника не найден: {file_path}")
        raise FileNotFoundError(f"Файл справочника не найден: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except IOError as e:
        logging.error(f"Ошибка чтения файла справочника {file_path}: {e}")
        raise IOError(f"Ошибка чтения файла справочника {file_path}: {e}")


# Шаблон промпта для детального извлечения данных
# prompt_template=""" ... было удалено ... """

def build_detailed_extraction_prompt(
    input_message: str, 
    cultures_content: str, 
    operations_content: str, 
    departments_content: str, 
    current_date: str | None = None
) -> str:
    """Формирует промпт для извлечения детальных данных из агро-отчета.

    Args:
        input_message: Текст сообщения.
        cultures_content: Содержимое файла со списком культур.
        operations_content: Содержимое файла со списком операций.
        departments_content: Содержимое файла со списком подразделений.
        current_date: Текущая дата в формате YYYY-MM-DD. Если None, используется сегодняшняя.

    Returns:
        Готовый текст промпта для LLM.
    """
    if current_date is None:
        current_date = datetime.date.today().isoformat()
        
    return DETAILED_EXTRACTION_PROMPT.format(
        input_message=input_message,
        cultures_content=cultures_content,
        operations_content=operations_content,
        departments_content=departments_content,
        current_date=current_date
    )

