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

    if not all_extracted_data:
        logging.warning("Данные не были извлечены ни из одного сообщения.")
        return None # Возвращаем None, если список пуст

    return all_extracted_data # Возвращаем список извлеченных данных 