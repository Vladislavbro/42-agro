import logging
# import json # Больше не нужен для вывода
import os
import asyncio
import sqlite3 # Добавляем для работы с БД
import datetime # Для отметки времени обработки

from app.config import REPORT_OUTPUT_PATH, BASE_DIR # Импортируем путь к отчету и базовую директорию
from app.utils.google_drive_uploader import upload_to_drive # Раскомментировано
# from data.test_messages import TEST_MESSAGES # Больше не используем тестовые сообщения
from app.llm_integration.processor import process_batch_async # Новая асинхронная функция

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Путь к базе данных парсера
DB_PATH = os.path.join(BASE_DIR, 'app', 'parser', 'messages.db')

def get_unprocessed_messages():
    """Извлекает необработанные сообщения из базы данных."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Выбираем id и text сообщений, где processed_at еще не установлен
        cursor.execute("SELECT id, text FROM messages WHERE processed_at IS NULL")
        messages = cursor.fetchall() # Получаем список кортежей (id, text)
        logging.info(f"Найдено {len(messages)} необработанных сообщений.")
        return messages
    except sqlite3.Error as e:
        logging.error(f"Ошибка при чтении из БД {DB_PATH}: {e}")
        return [] # Возвращаем пустой список при ошибке
    finally:
        if conn:
            conn.close()

def mark_messages_as_processed(message_ids: list[str]):
    """Помечает сообщения как обработанные в базе данных."""
    if not message_ids:
        return
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat() # Текущее время в ISO формате
        # Подготавливаем данные для обновления: список кортежей (время, id)
        update_data = [(now, msg_id) for msg_id in message_ids]
        # Используем executemany для обновления нескольких строк одним запросом
        cursor.executemany("UPDATE messages SET processed_at = ? WHERE id = ?", update_data)
        conn.commit() # Сохраняем изменения
        logging.info(f"Отмечено как обработанные {len(message_ids)} сообщений.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при обновлении БД {DB_PATH}: {e}")
        if conn:
            conn.rollback() # Откатываем изменения при ошибке
    finally:
        if conn:
            conn.close()

async def main():
    logging.info(f"Проверка базы данных на наличие необработанных сообщений: {DB_PATH}...")
    unprocessed_messages = get_unprocessed_messages()

    if not unprocessed_messages:
        logging.info("Нет новых сообщений для обработки.")
        return

    message_texts = [msg[1] for msg in unprocessed_messages]
    message_ids = [msg[0] for msg in unprocessed_messages]

    # Определяем путь к выходному файлу (можно сделать динамическим, если нужно)
    output_file = REPORT_OUTPUT_PATH
    logging.info(f"Запуск асинхронной обработки {len(message_texts)} сообщений. Результат будет сохранен в {output_file}")

    # Вызываем process_batch_async, передавая тексты и путь к файлу
    # Устанавливаем run_quality_test=False, т.к. эталонного файла пока нет
    processed_data_list = await process_batch_async(
        messages=message_texts, 
        output_filename=output_file, 
        run_quality_test=False 
    )

    if processed_data_list is not None:
        logging.info(f"Асинхронная пакетная обработка сообщений завершена. Получено {len(processed_data_list) if isinstance(processed_data_list, list) else 'N/A'} записей.")
        mark_messages_as_processed(message_ids)
        
        # Логика загрузки на Google Drive 
        report_created = os.path.exists(output_file) and os.path.getsize(output_file) > 0
        if report_created:
            logging.info(f"Файл отчета {output_file} создан/обновлен.")
            logging.info(f"Запуск загрузки файла {output_file} на Google Drive...")
            try:
                # Запускаем загрузку в отдельном потоке, чтобы не блокировать async loop
                # (PyDrive2, похоже, не полностью async-совместима)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, upload_to_drive, output_file)
                # upload_to_drive(output_file) # Старый синхронный вызов
                # logging.info("Загрузка файла инициирована.") # Можно добавить, если нужно
            except Exception as e:
                 logging.error(f"Ошибка при попытке запуска загрузки на Google Drive: {e}")
        else:
             logging.warning("Файл отчета пуст или не создан, загрузка на Google Drive отменена.")
    else:
        logging.error("Асинхронная пакетная обработка сообщений завершилась с ошибкой.")

if __name__ == "__main__":
    asyncio.run(main())

