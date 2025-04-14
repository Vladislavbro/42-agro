# Код для формирования промптов для LLM 

import logging
import os

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


# TODO: Добавить функции build_detailed_extraction_prompt и build_structure_analysis_prompt 