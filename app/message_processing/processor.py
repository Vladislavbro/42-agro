import datetime
import logging
import pandas as pd
import os

from app import config
from app.llm_integration.client import TextGenerationClient
from app.llm_integration.prompt_builder import load_mapping_file, build_detailed_extraction_prompt
from app.llm_integration.extractor import extract_json_list


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


def process_batch(messages: list[str], output_filename: str):
    """
    Обрабатывает список сообщений и сохраняет результаты в Excel файл.
    """
    total_messages = len(messages)
    logging.info(f"Начало пакетной обработки {total_messages} сообщений...")

    output_dir = os.path.dirname(output_filename)
    os.makedirs(output_dir, exist_ok=True)

    startrow = 0
    header_written = False
    data_written = False

    try:
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            for i, message in enumerate(messages):
                logging.info(f"--- Обработка сообщения {i+1}/{total_messages} ---")
                result = process_single_message(message)

                if result:
                    logging.info(f"Сообщение {i+1}/{total_messages} обработано успешно, извлечено {len(result)} записей.")
                    df_message = pd.DataFrame(result)

                    df_message.to_excel(writer,
                                        sheet_name='Results',
                                        startrow=startrow,
                                        index=False,
                                        header=not header_written)
                    data_written = True
                    header_written = True

                    startrow += len(df_message) + 1
                else:
                    logging.warning(f"Не удалось обработать сообщение {i+1}/{total_messages} или извлечь из него данные.")
                logging.info(f"--- Завершение обработки сообщения {i+1}/{total_messages} ---")

            logging.info("Пакетная обработка всех сообщений завершена.")
            if data_written:
                logging.info(f"Результаты успешно сохранены в файл: {output_filename}")
            else:
                logging.warning("Нет данных для сохранения в Excel.")
        return True
    except Exception as e:
        logging.error(f"Ошибка при записи в Excel: {e}")
        return False 