import logging
import json # Добавим импорт json для красивого вывода
import os
import asyncio # Добавлено

from app.utils.google_drive_uploader import upload_to_drive
from data.test_messages import TEST_MESSAGES # Импортируем тестовые сообщения из корневой папки data
from app.message_processing.processor import process_batch_async # Новая асинхронная функция

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main(): # Оборачиваем в async def
    output_filename = "data/reports/processing_results.xlsx"

    # Вызываем АСИНХРОННУЮ функцию пакетной обработки
    # success = process_batch(TEST_MESSAGES, output_filename) # Старый вызов
    logging.info("Запуск асинхронной обработки...")
    success = await process_batch_async(TEST_MESSAGES, output_filename)

    if success:
        logging.info("Асинхронная пакетная обработка сообщений завершена успешно.")
        # Загрузка на Google Drive происходит здесь, если обработка прошла успешно
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            logging.info(f"Запуск загрузки файла {output_filename} на Google Drive...")
            # upload_to_drive(output_filename) # Раскомментировать для включения загрузки
            logging.info("Загрузка (симуляция) завершена.") # Заглушка
        else:
            logging.warning("Файл отчета пуст или не создан после асинхронной обработки, загрузка на Google Drive отменена.")
    else:
        logging.error("Асинхронная пакетная обработка сообщений завершилась с ошибкой.")

if __name__ == "__main__":
    # Запускаем асинхронную функцию main
    asyncio.run(main())

