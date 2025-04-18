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


# Синхронные функции process_single_message и process_batch были удалены


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


async def process_batch_async(messages: list[str], run_quality_test: bool = True) -> list | None:
    """
    Асинхронно обрабатывает список сообщений и возвращает список извлеченных JSON-объектов.
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
        return None

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
        return None
    except Exception as e:
        logging.error(f"Критическая ошибка при загрузке справочников или промпта: {e}")
        return None

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
    successful_results_per_message = [] # Список для хранения успешных результатов по сообщениям

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logging.error(f"Ошибка при обработке сообщения {i+1}: {result}")
            failed_count += 1
            successful_results_per_message.append(None) # Добавляем placeholder для неудач
        elif result is None or not result: # Также проверяем на пустой список
            if result is None:
                 logging.warning(f"Сообщение {i+1} обработано, но данные не извлечены (вернулся None).")
            else: # result == []
                 logging.info(f"Сообщение {i+1} обработано, но LLM не вернул структурированных данных.")
            failed_count += 1 # Считаем как неудачу, если данные не извлечены
            successful_results_per_message.append(None) # Добавляем placeholder
        else:
            # Результат - это список словарей (JSON объектов)
            all_extracted_data.extend(result) # Собираем все для определения колонок
            successful_results_per_message.append(result) # Сохраняем результат для этого сообщения
            successful_count += 1

    logging.info(f"Обработка завершена. Успешно: {successful_count}, Неудачно/Нет данных: {failed_count}")

    if not all_extracted_data:
        logging.warning("Нет данных для сохранения в Excel после асинхронной обработки.")
        processing_successful = False
    else:
        record_count = len(all_extracted_data)
        logging.info(f"Подготовка {record_count} извлеченных записей (сгруппированных по сообщениям) для сохранения в Excel...")
        try:
            # 1. Определяем полный набор колонок на основе всех данных
            df_temp = pd.DataFrame(all_extracted_data)
            all_columns = df_temp.columns
            del df_temp # Освобождаем память

            # 2. Создаем пустой DataFrame (одна строка с NaN) с нужными колонками
            empty_df = pd.DataFrame([[None] * len(all_columns)], columns=all_columns)

            # 3. Создаем список DataFrame'ов для объединения
            dfs_to_concat = []
            for message_result in successful_results_per_message:
                if message_result: # Если для этого сообщения были успешные результаты
                    df_message = pd.DataFrame(message_result)
                    # Переиндексируем, чтобы гарантировать наличие всех колонок и их порядок
                    df_message = df_message.reindex(columns=all_columns)
                    dfs_to_concat.append(df_message)
                    dfs_to_concat.append(empty_df) # Добавляем пустую строку ПОСЛЕ данных сообщения

            # 4. Удаляем последнюю пустую строку, если она есть
            if dfs_to_concat:
                dfs_to_concat.pop()

            # 5. Объединяем DataFrame'ы, если есть что объединять
            if dfs_to_concat:
                df_final = pd.concat(dfs_to_concat, ignore_index=True)
            else:
                # Если после фильтрации не осталось данных (маловероятно, если all_extracted_data не пусто, но для надежности)
                df_final = pd.DataFrame(columns=all_columns) # Создаем пустой DataFrame с колонками

            # Сохраняем результат
            logging.info(f"Сохранение итогового DataFrame в Excel...")
            output_dir = os.path.dirname(output_filename)
            os.makedirs(output_dir, exist_ok=True)

            with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                df_final.to_excel(writer, sheet_name='Results', index=False, header=True)

            logging.info(f"Результаты успешно сохранены в файл: {output_filename}")
            processing_successful = True

        except Exception as e:
            logging.error(f"Ошибка при обработке данных и записи в Excel: {e}")
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