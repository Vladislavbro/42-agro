import logging
import json # Добавим импорт json для красивого вывода
import os
import asyncio # Добавлено

from app.config import REPORT_OUTPUT_PATH # Импортируем путь к отчету
from app.utils.google_drive_uploader import upload_to_drive
from data.test_messages import TEST_MESSAGES # Импортируем тестовые сообщения из корневой папки data
from app.llm_integration.processor import process_batch_async # Новая асинхронная функция

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main(): # Оборачиваем в async def

    # Вызываем АСИНХРОННУЮ функцию пакетной обработки
    logging.info("Запуск асинхронной обработки...")
    success = await process_batch_async(TEST_MESSAGES, REPORT_OUTPUT_PATH) # Используем переменную из конфига

    if success:
        logging.info("Асинхронная пакетная обработка сообщений завершена успешно.")
        # Загрузка на Google Drive происходит здесь, если обработка прошла успешно
        # if os.path.exists(REPORT_OUTPUT_PATH) and os.path.getsize(REPORT_OUTPUT_PATH) > 0: # Используем переменную из конфига
        #     logging.info(f"Запуск загрузки файла {REPORT_OUTPUT_PATH} на Google Drive...") # Используем переменную из конфига
        #     # upload_to_drive(REPORT_OUTPUT_PATH) # Раскомментировать для включения загрузки
        #     logging.info("Загрузка (симуляция) завершена.") # Заглушка
        # else:
        #     logging.warning("Файл отчета пуст или не создан после асинхронной обработки, загрузка на Google Drive отменена.")
    else:
        logging.error("Асинхронная пакетная обработка сообщений завершилась с ошибкой.")

if __name__ == "__main__":
    # Запускаем асинхронную функцию main
    asyncio.run(main())

