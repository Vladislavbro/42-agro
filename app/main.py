import datetime
import logging
import json # Добавим импорт json для красивого вывода

# Импортируем наши модули
from app import config
from app.llm_integration.client import TextGenerationClient
from app.llm_integration.prompt_builder import load_mapping_file, build_detailed_extraction_prompt
from app.llm_integration.extractor import extract_json_list

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_single_message(message: str):
    """
    Обрабатывает одно сообщение: строит промпт, вызывает LLM, извлекает JSON.
    """
    logging.info("Инициализация клиента LLM...")
    try:
        llm_client = TextGenerationClient()
        logging.info(f"Клиент LLM инициализирован (Провайдер: {config.PRIMARY_LLM_PROVIDER})")
    except Exception as e:
        logging.error(f"Ошибка инициализации клиента LLM: {e}")
        return None

    logging.info("Загрузка справочников...")
    try:
        cultures_content = load_mapping_file(config.CULTURES_FILE_PATH)
        operations_content = load_mapping_file(config.OPERATIONS_FILE_PATH)
        # departments загружается как json строка
        with open(config.DEPARTMENTS_FILE_PATH, 'r', encoding='utf-8') as f:
            departments_content = f.read()
        logging.info("Справочники успешно загружены.")
    except FileNotFoundError as e:
        logging.error(f"Ошибка: Файл справочника не найден - {e}")
        return None
    except Exception as e:
        logging.error(f"Ошибка при загрузке справочников: {e}")
        return None

    current_date = datetime.date.today().strftime('%Y-%m-%d')
    logging.info(f"Текущая дата: {current_date}")

    logging.info("Построение промпта...")
    try:
        prompt = build_detailed_extraction_prompt(
            input_message=message,
            cultures_content=cultures_content,
            operations_content=operations_content,
            departments_content=departments_content, # Передаем JSON строку
            current_date=current_date
        )
        logging.info("Промпт успешно построен.")
        # logging.debug(f"Сгенерированный промпт:\n{prompt}") # Можно раскомментировать для отладки
    except Exception as e:
        logging.error(f"Ошибка при построении промпта: {e}")
        return None

    logging.info("Отправка запроса к LLM...")
    llm_response = llm_client.generate_response(prompt)

    if llm_response:
        logging.info("Ответ от LLM получен.")
        # logging.debug(f"Ответ LLM (сырой):\n{llm_response}") # Можно раскомментировать для отладки
        logging.info("Извлечение JSON из ответа...")
        extracted_data = extract_json_list(llm_response)
        if extracted_data:
            logging.info("JSON успешно извлечен.")
            return extracted_data
        else:
            logging.error("Не удалось извлечь JSON из ответа LLM.")
            logging.warning(f"""Ответ LLM, из которого не удалось извлечь JSON:
            {llm_response}""")
            return None
    else:
        logging.error("Не удалось получить ответ от LLM.")
        return None

if __name__ == "__main__":
    # --- Тестовое сообщение ---
    test_message = """
    Пахота под сах св
    По Пу 88/329
    Отд 11 23/60
    Отд 12 34/204
    Отд 16 31/65

    Пахота под мн тр
    По Пу 10/438
    Отд 17 10/80

    Чизел под оз ячмень
    По Пу 71/528
    Отд 11 71/130

    2-е диск под сах св
    По Пу 80/1263
    Отд 12 80/314

    2-е диск под оз ячмень
    По Пу 97/819
    Отд 17 97/179

    Диск кук силос
    По Пу 43/650
    Отд 11 33/133
    Отд 12 10/148

    Выкаш отц форм под/г
    Отд 12 10/22

    Уборка сах св
    Отд 12 16/16
    Вал 473920
    Урож 296,2
    Диг - 19,19
    Оз - 5,33"
    """
    # test_message = "Сидоров обработал 50 гектар кукурузы гербицидом Раундап на тракторе Кировец К-700 в Северном отделении вчера"
    # test_message = "Петров ВВ, 12 га, Дискование БДМ 6х4, МТЗ-1221, отд. Южное, 16.05.2024"

    logging.info(f"Обработка тестового сообщения: '{test_message}'")

    result = process_single_message(test_message)

    if result:
        logging.info("--- Результат обработки ---")
        # Используем json.dumps для красивого вывода списка словарей
        print(json.dumps(result, indent=2, ensure_ascii=False))
        logging.info("Обработка завершена успешно.")
    else:
        logging.error("Обработка сообщения завершилась с ошибкой.")
