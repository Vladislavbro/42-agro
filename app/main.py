import logging
import json # Добавим импорт json для красивого вывода
import os
import asyncio # Добавлено

from app.config import REPORT_OUTPUT_PATH # Импортируем путь к отчету
from app.utils.google_drive_uploader import upload_to_drive
from data.test_messages import TEST_MESSAGES # Импортируем тестовые сообщения из корневой папки data
from app.message_processing.processor import process_batch_async # Новая асинхронная функция
from fastapi import FastAPI
from app.core.settings import get_settings
from app.api import health, messages, reports  # подключаем всё

settings = get_settings()

app = FastAPI(
    title="42‑Agro API",
    description="MVP backend для агро‑отчётов",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(health.router)
app.include_router(messages.router)
app.include_router(reports.router)


# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main(): # Оборачиваем в async def

    # Вызываем АСИНХРОННУЮ функцию пакетной обработки
    logging.info("Запуск асинхронной обработки...")
    # Вызываем без output_filename, результат - список JSON или None
    extracted_data = await process_batch_async(TEST_MESSAGES)

    # Проверяем, вернула ли функция список (успех) или None (ошибка/нет данных)
    if extracted_data is not None:
        logging.info(f"Асинхронная пакетная обработка сообщений завершена успешно. Извлечено {len(extracted_data)} записей.")
        return extracted_data
    else:
        logging.error("Асинхронная пакетная обработка сообщений завершилась с ошибкой или не извлекла данных.")

if __name__ == "__main__":
    # Запускаем асинхронную функцию main и сохраняем результат
    result_data = asyncio.run(main())
    # Печатаем результат, если он не None
    if result_data is not None:
        print("\n--- Результат выполнения main() ---")
        # Используем json.dumps для красивого вывода
        print(json.dumps(result_data, indent=2, ensure_ascii=False))

