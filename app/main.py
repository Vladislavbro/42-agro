import datetime
import logging
import json # Добавим импорт json для красивого вывода
import pandas as pd # Добавим импорт pandas

# Импортируем наши модули
from app import config
from app.llm_integration.client import TextGenerationClient
from app.llm_integration.prompt_builder import load_mapping_file, build_detailed_extraction_prompt
from app.llm_integration.extractor import extract_json_list
from data.test_messages import TEST_MESSAGES # Импортируем тестовые сообщения из корневой папки data

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_single_message(message: str):
    """
    Обрабатывает одно сообщение: строит промпт, вызывает LLM, извлекает JSON.
    """
    logging.info("Инициализация клиента LLM...")
    try:
        llm_client = TextGenerationClient()
        # Уточненное сообщение с провайдером и моделью из объекта клиента
        logging.info(f"Клиент LLM инициализирован: Провайдер='{llm_client.provider}', Модель='{llm_client.model_name}'")
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
    # Список для хранения всех извлеченных данных
    all_extracted_data = []
    total_messages = len(TEST_MESSAGES)
    logging.info(f"Начало пакетной обработки {total_messages} сообщений...")

    for i, message in enumerate(TEST_MESSAGES):
        logging.info(f"--- Обработка сообщения {i+1}/{total_messages} ---")
        # logging.debug(f"Текст сообщения:\n{message}") # Можно раскомментировать для отладки
        result = process_single_message(message)

        if result:
            # Если извлечение успешно, добавляем результаты в общий список
            # result - это список словарей, поэтому используем extend
            all_extracted_data.extend(result)
            logging.info(f"Сообщение {i+1}/{total_messages} обработано успешно, извлечено {len(result)} записей.")
        else:
            logging.warning(f"Не удалось обработать сообщение {i+1}/{total_messages} или извлечь из него данные.")
        logging.info(f"--- Завершение обработки сообщения {i+1}/{total_messages} ---")

    logging.info("Пакетная обработка всех сообщений завершена.")

    # Сохранение результатов в Excel, если есть данные
    if all_extracted_data:
        logging.info(f"Начинаем сохранение {len(all_extracted_data)} извлеченных записей в Excel...")
        try:
            df = pd.DataFrame(all_extracted_data)
            output_filename = "data/reports/processing_results.xlsx"
            df.to_excel(output_filename, index=False, engine='openpyxl')
            logging.info(f"Результаты успешно сохранены в файл: {output_filename}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении результатов в Excel: {e}")
            # В случае ошибки сохранения, выведем данные в консоль как JSON для отладки
            logging.info("--- Резервный вывод данных в формате JSON ---")
            print(json.dumps(all_extracted_data, indent=2, ensure_ascii=False))
    else:
        logging.warning("Нет данных для сохранения в Excel.")
