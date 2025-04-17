# Модуль для извлечения JSON из текстовых ответов LLM

import json
import logging
from typing import List, Dict, Any, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _clean_and_parse_json(llm_response: str) -> Any:
    """Вспомогательная функция для очистки и парсинга JSON строки."""
    if not isinstance(llm_response, str):
        logger.error(f"Ошибка: На вход ожидалась строка, получено {type(llm_response)}")
        return None
        
    json_string = llm_response.strip()
    
    # Удаляем ```json и ```, если они есть
    if json_string.startswith("```json"):
        json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]
    elif json_string.startswith("```"):
         if json_string.endswith("```"):
            json_string = json_string[3:-3]

    json_string = json_string.strip() # Повторный strip после удаления маркеров

    try:
        parsed_data = json.loads(json_string)
        return parsed_data
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        logger.debug(f"Строка, которую не удалось распарсить: {json_string[:500]}...") # Логируем начало строки
        return None
    except Exception as e: # Ловим другие возможные ошибки при парсинге
        logger.error(f"Неожиданная ошибка при парсинге JSON: {e}")
        logger.debug(f"Строка, вызвавшая ошибку: {json_string[:500]}...")
        return None

def extract_json_list(llm_response: str) -> Optional[List[Dict[str, Any]]]:
    """
    Извлекает JSON-список словарей из текстового ответа LLM.

    Очищает ответ от маркеров ```json ... ``` и парсит его.
    Проверяет, что результат является списком.

    Args:
        llm_response: Текстовый ответ от LLM.

    Returns:
        Список словарей или None в случае ошибки или если результат не список.
    """
    parsed_data = _clean_and_parse_json(llm_response)
    
    if parsed_data is None:
        return None

    if not isinstance(parsed_data, list):
        logger.error(f"Ошибка: Ожидался JSON-список, но получен {type(parsed_data)}.")
        logger.debug(f"Данные: {parsed_data}")
        return None
    
    # Простая проверка, что элементы списка - словари (опционально, но полезно)
    if parsed_data and not all(isinstance(item, dict) for item in parsed_data):
        logger.warning("Предупреждение: Не все элементы в извлеченном списке являются словарями.")
        # Решаем, возвращать как есть или считать ошибкой. Пока возвращаем.

    logger.info(f"Успешно извлечен JSON-список с {len(parsed_data)} элементами.")
    return parsed_data 