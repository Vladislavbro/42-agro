import datetime
import logging
import pandas as pd
import os
import asyncio
import aiohttp
import itertools
import json # Добавлено для llm_settings

from app import config
from app.llm_integration.client import TextGenerationClient
from app.llm_integration.prompt_builder import load_mapping_file, build_detailed_extraction_prompt
from app.llm_integration.extractor import extract_json_list
from app.llm_integration.constants import DETAILED_EXTRACTION_PROMPT # Добавлен импорт промпта
from app.utils.quality_test import save_quality_test_results # Добавлен импорт функции теста


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


async def process_single_message_async(
    message_index: int,
    message: str,
    llm_client: TextGenerationClient,
    session: aiohttp.ClientSession,
    cultures_content: str,
    operations_content: str,
    departments_content: str,
    current_date: str,
    base_prompt: str # Добавлен параметр для передачи промпта
) -> list | None:
    """
    Асинхронно обрабатывает одно сообщение.
    Принимает инициализированный клиент, сессию и загруженные справочники.
    """
    logging.info(f"[Msg {message_index+1}] Построение промпта...")
    try:
        # Используем переданный базовый промпт
        prompt = base_prompt.format(
            input_message=message,
            cultures_content=cultures_content,
            operations_content=operations_content,
            departments_content=departments_content,
            current_date=current_date
        )
        # logging.debug(f"[Msg {message_index+1}] Сгенерированный промпт:\n{prompt}")
        logging.info(f"[Msg {message_index+1}] Промпт успешно построен.")
    except Exception as e:
        logging.error(f"[Msg {message_index+1}] Ошибка при построении промпта: {e}")
        return None # Возвращаем None при ошибке

    logging.info(f"[Msg {message_index+1}] Отправка асинхронного запроса к LLM...")
    # Передаем сформированный промпт
    llm_response = await llm_client.generate_response_async(session, prompt)

    if llm_response:
        logging.info(f"[Msg {message_index+1}] Ответ от LLM получен.")
        # logging.debug(f"[Msg {message_index+1}] Ответ LLM (сырой):\n{llm_response}")
        logging.info(f"[Msg {message_index+1}] Извлечение JSON из ответа...")
        extracted_data = extract_json_list(llm_response)
        if extracted_data:
            logging.info(f"[Msg {message_index+1}] JSON успешно извлечен ({len(extracted_data)} записей).")
            return extracted_data
        else:
            logging.error(f"[Msg {message_index+1}] Не удалось извлечь JSON из ответа LLM.")
            log_message = f"[Msg {message_index+1}] Ответ LLM, из которого не удалось извлечь JSON:\n{llm_response}"
            logging.warning(log_message) # Новый вариант
            return None # Возвращаем None при ошибке
    else:
        logging.error(f"[Msg {message_index+1}] Не удалось получить ответ от LLM.")
        return None # Возвращаем None при ошибке


async def process_batch_async(messages: list[str], output_filename: str, run_quality_test: bool = True) -> bool:
    """
    Асинхронно обрабатывает список сообщений, сохраняет результаты в Excel файл
    и опционально запускает тест качества.
    """
    total_messages = len(messages)
    logging.info(f"Начало АСИНХРОННОЙ пакетной обработки {total_messages} сообщений...")

    # 1. Инициализация LLM клиента (один раз)
    logging.info("Инициализация клиента LLM...")
    try:
        llm_client = TextGenerationClient()
        logging.info(f"Клиент LLM инициализирован: Провайдер='{llm_client.provider}', Модель='{llm_client.model_name}'")
        # Собираем настройки LLM для последующего сохранения
        llm_settings = {
            "provider": llm_client.provider,
            "model_name": llm_client.model_name,
            "temperature": llm_client.temperature, # Теперь берем сохраненную температуру
            # Добавьте другие релевантные настройки, если они есть в TextGenerationClient
            # и сохраняются в self при инициализации
            # "max_tokens": getattr(llm_client, 'max_tokens', None),
            # "top_p": getattr(llm_client, 'top_p', None),
        }
    except Exception as e:
        logging.error(f"Критическая ошибка: Не удалось инициализировать клиента LLM: {e}")
        return False

    # 2. Загрузка справочников и базового промпта (один раз)
    logging.info("Загрузка справочников и базового промпта...")
    try:
        cultures_content = load_mapping_file(config.CULTURES_FILE_PATH)
        operations_content = load_mapping_file(config.OPERATIONS_FILE_PATH)
        with open(config.DEPARTMENTS_FILE_PATH, 'r', encoding='utf-8') as f:
            departments_content = f.read()
        # Используем импортированный DETAILED_EXTRACTION_PROMPT как базовый
        base_prompt_template = DETAILED_EXTRACTION_PROMPT
        logging.info("Справочники и базовый промпт успешно загружены.")
    except FileNotFoundError as e:
        logging.error(f"Критическая ошибка: Файл справочника не найден - {e}")
        return False
    except Exception as e:
        logging.error(f"Критическая ошибка при загрузке справочников или промпта: {e}")
        return False

    current_date = datetime.date.today().strftime('%Y-%m-%d')
    logging.info(f"Текущая дата: {current_date}")

    # 3. Создание задач для асинхронной обработки
    tasks = []
    connector = aiohttp.TCPConnector(limit_per_host=config.MAX_CONCURRENT_REQUESTS) # Ограничение одновременных запросов
    async with aiohttp.ClientSession(connector=connector) as session:
        logging.info(f"Создание {total_messages} асинхронных задач для обработки сообщений...")
        for i, message in enumerate(messages):
            task = asyncio.create_task(
                process_single_message_async(
                    message_index=i,
                    message=message,
                    llm_client=llm_client,
                    session=session,
                    cultures_content=cultures_content,
                    operations_content=operations_content,
                    departments_content=departments_content,
                    current_date=current_date,
                    base_prompt=base_prompt_template # Передаем базовый промпт
                ),
                name=f"ProcessMsg-{i+1}"
            )
            tasks.append(task)

        # 4. Запуск и ожидание выполнения всех задач
        logging.info(f"Запуск {len(tasks)} задач параллельно (макс. {config.MAX_CONCURRENT_REQUESTS} одновременных)...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logging.info("Все асинхронные задачи завершены.")

    # 5. Обработка результатов
    all_extracted_data = []
    successful_count = 0
    failed_count = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logging.error(f"Ошибка при обработке сообщения {i+1}: {result}")
            failed_count += 1
        elif result is None:
            logging.warning(f"Сообщение {i+1} обработано, но данные не извлечены (вернулся None).")
            failed_count += 1 # Считаем как неудачу, если данные не извлечены
        else:
            # Результат - это список словарей (JSON объектов)
            all_extracted_data.extend(result)
            successful_count += 1

    logging.info(f"Обработка завершена. Успешно: {successful_count}, Неудачно/Нет данных: {failed_count}")

    # 6. Сохранение результатов в Excel
    processing_successful = False
    if not all_extracted_data:
        logging.warning("Нет данных для сохранения в Excel после асинхронной обработки.")
        # Если файл уже существует от предыдущего запуска, его стоит удалить или обработать иначе
        # Здесь просто считаем, что обработка прошла, но не успешно с точки зрения наличия данных
        processing_successful = False
    else:
        logging.info(f"Сохранение {len(all_extracted_data)} извлеченных записей в Excel...")
        output_dir = os.path.dirname(output_filename)
        os.makedirs(output_dir, exist_ok=True)
        try:
            df_final = pd.DataFrame(all_extracted_data)
            with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                df_final.to_excel(writer, sheet_name='Results', index=False, header=True)
            logging.info(f"Результаты успешно сохранены в файл: {output_filename}")
            processing_successful = True
        except Exception as e:
            logging.error(f"Ошибка при записи итогового DataFrame в Excel: {e}")
            processing_successful = False

    # 7. Запуск теста качества (если обработка прошла успешно и флаг установлен)
    if processing_successful and run_quality_test:
        logging.info("Запуск теста качества...")
        # Определяем пути для теста
        # Используем config для путей, если они там определены, иначе строим относительно корня
        project_root = config.BASE_DIR # Предполагаем, что BASE_DIR определен в config
        benchmark_file_path = getattr(config, 'BENCHMARK_FILE_PATH', 
                                      os.path.join(project_root, "data", "reports", "benchmark-report.xlsx"))
        quality_test_output_dir = getattr(config, 'QUALITY_TEST_DIR', 
                                            os.path.join(project_root, "llm_quality_tests"))
        
        # Убедимся, что директория для тестов существует
        os.makedirs(quality_test_output_dir, exist_ok=True)

        # Вызываем функцию сохранения результатов теста
        save_quality_test_results(
            benchmark_file_path=benchmark_file_path,
            processing_file_path=output_filename, # Файл, который только что создали
            output_dir_base=quality_test_output_dir,
            prompt_text=base_prompt_template, # Передаем шаблон промпта, а не форматированный
            llm_settings=llm_settings, # Передаем собранные настройки
            provider_name=llm_client.provider # <<< Добавлено имя провайдера
        )
    elif not processing_successful:
         logging.warning("Пропускаем тест качества, так как не было данных для сохранения в Excel.")
    elif not run_quality_test:
         logging.info("Пропускаем тест качества, так как флаг run_quality_test=False.")

    return processing_successful # Возвращаем True, если Excel файл был успешно создан 