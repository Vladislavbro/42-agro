import logging
import json # Добавим импорт json для красивого вывода
import pandas as pd # Добавим импорт pandas
import os

# Импортируем наши модули
# Удалены импорты TextGenerationClient, load_mapping_file, build_detailed_extraction_prompt, extract_json_list, config
# Удален импорт datetime
from app.utils.google_drive_uploader import upload_to_drive
from data.test_messages import TEST_MESSAGES # Импортируем тестовые сообщения из корневой папки data
from app.message_processing.processor import process_single_message # Импортируем функцию обработки

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    total_messages = len(TEST_MESSAGES)
    logging.info(f"Начало пакетной обработки {total_messages} сообщений...")

    output_filename = "data/reports/processing_results.xlsx"
    output_dir = os.path.dirname(output_filename)
    os.makedirs(output_dir, exist_ok=True)

    startrow = 0
    header_written = False
    data_written = False # Флаг для проверки, были ли записаны какие-либо данные

    # Используем ExcelWriter для добавления DataFrame'ов
    try:
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            for i, message in enumerate(TEST_MESSAGES):
                logging.info(f"--- Обработка сообщения {i+1}/{total_messages} ---")
                result = process_single_message(message)

                if result:
                    logging.info(f"Сообщение {i+1}/{total_messages} обработано успешно, извлечено {len(result)} записей.")
                    df_message = pd.DataFrame(result)

                    # Запись DataFrame на лист Excel
                    df_message.to_excel(writer,
                                        sheet_name='Results', # Укажем имя листа
                                        startrow=startrow,
                                        index=False,
                                        header=not header_written) # Записываем заголовок только первый раз
                    data_written = True # Отмечаем, что данные были записаны
                    header_written = True # Заголовок теперь записан

                    # Обновляем startrow для следующего DataFrame, добавляя 1 для пустой строки
                    startrow += len(df_message) + 1
                else:
                    logging.warning(f"Не удалось обработать сообщение {i+1}/{total_messages} или извлечь из него данные.")
                logging.info(f"--- Завершение обработки сообщения {i+1}/{total_messages} ---")

            logging.info("Пакетная обработка всех сообщений завершена.")
            if data_written:
                 logging.info(f"Результаты успешно сохранены в файл: {output_filename}")
            else:
                logging.warning("Нет данных для сохранения в Excel.")
                # Если данные не были записаны, менеджер контекста ExcelWriter сохранит пустой файл.
                # Можно его удалить или оставить пустым. Пока оставим пустым.

    except Exception as e:
        logging.error(f"Ошибка при записи в Excel: {e}")
        # Резервный вывод JSON здесь может быть менее полезен, так как данные не агрегировались.
        # Возможно, стоит просто записать ошибку и выйти или попытаться сохранить то, что было обработано до ошибки.
        # Пока просто логируем ошибку.
