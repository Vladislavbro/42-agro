import logging
import json # Добавим импорт json для красивого вывода
import pandas as pd # Добавим импорт pandas
import os

# Импортируем наши модули
# Удалены импорты TextGenerationClient, load_mapping_file, build_detailed_extraction_prompt, extract_json_list, config
# Удален импорт datetime
from data.test_messages import TEST_MESSAGES # Импортируем тестовые сообщения из корневой папки data
from app.message_processing.processor import process_single_message # Импортируем функцию обработки

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            # Убедимся, что директория для сохранения существует
            output_dir = os.path.dirname(output_filename)
            os.makedirs(output_dir, exist_ok=True)
            df.to_excel(output_filename, index=False, engine='openpyxl')
            logging.info(f"Результаты успешно сохранены в файл: {output_filename}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении результатов в Excel: {e}")
            # В случае ошибки сохранения, выведем данные в консоль как JSON для отладки
            logging.info("--- Резервный вывод данных в формате JSON ---")
            print(json.dumps(all_extracted_data, indent=2, ensure_ascii=False))
    else:
        logging.warning("Нет данных для сохранения в Excel.")
