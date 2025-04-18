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

def get_unprocessed_messages(date_str: str | None = None):
    """
    Извлекает необработанные сообщения из базы данных.
    Если date_str указана (в формате YYYY-MM-DD), фильтрует по дате.
    Иначе извлекает все необработанные.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if date_str:
            # Фильтруем по дате, используя SQLite функцию DATE()
            # Выбираем id и text сообщений за указанную дату, где processed_at еще не установлен
            sql = "SELECT id, text FROM messages WHERE processed_at IS NULL AND DATE(timestamp) = ?"
            cursor.execute(sql, (date_str,))
            logging.info(f"Поиск необработанных сообщений за {date_str}...")
        else:
            # Выбираем все необработанные
            sql = "SELECT id, text FROM messages WHERE processed_at IS NULL"
            cursor.execute(sql)
            logging.info(f"Поиск всех необработанных сообщений...")
            
        messages = cursor.fetchall() # Получаем список кортежей (id, text)
        logging.info(f"Найдено {len(messages)} сообщений.")
        return messages
    except sqlite3.Error as e:
        logging.error(f"Ошибка при чтении из БД {DB_PATH}: {e}")
        return []
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

async def run_processing_for_date(date_str: str) -> dict:
    """
    Запускает обработку сообщений за указанную дату.

    Args:
        date_str: Дата в формате 'YYYY-MM-DD'.

    Returns:
        Словарь с результатом:
        { 'success': bool, 'report_path': str | None, 'processed_count': int, 'message': str }
    """
    logging.info(f"--- Запуск обработки для даты: {date_str} ---")
    result_status = {
        'success': False,
        'report_path': None,
        'processed_count': 0,
        'message': ''
    }

    unprocessed_messages = get_unprocessed_messages(date_str)

    if not unprocessed_messages:
        result_status['success'] = True
        result_status['message'] = f"Нет необработанных сообщений за {date_str}."
        logging.info(result_status['message'])
        return result_status

    message_texts = [msg[1] for msg in unprocessed_messages]
    message_ids = [msg[0] for msg in unprocessed_messages]
    result_status['processed_count'] = len(message_ids)

    # --- Определяем путь к выходному файлу для этой даты ---
    # Базовая папка для отчетов берется из config (папка data/reports)
    report_dir = os.path.dirname(REPORT_OUTPUT_PATH)
    # Расширение файла берем из config (по умолчанию .xlsx)
    report_ext = os.path.splitext(os.path.basename(REPORT_OUTPUT_PATH))[1]
    # Новое имя файла
    output_filename = os.path.join(report_dir, f"Отчет_{date_str}{report_ext}")
    result_status['report_path'] = output_filename # Сохраняем путь для возврата
    # --- Конец определения пути --- 
    
    logging.info(f"Запуск LLM обработки {len(message_texts)} сообщений. Результат будет сохранен в {output_filename}")

    processed_data_list = await process_batch_async(
        messages=message_texts,
        output_filename=output_filename, # Передаем новое имя файла
        run_quality_test=False
    )

    if processed_data_list is not None:
        logging.info(f"LLM обработка сообщений завершена. Получено {len(processed_data_list) if isinstance(processed_data_list, list) else 'N/A'} записей.")
        mark_messages_as_processed(message_ids)
        
        report_created = os.path.exists(output_filename) and os.path.getsize(output_filename) > 0
        if report_created:
            logging.info(f"Файл отчета {output_filename} создан/обновлен.")
            result_status['success'] = True
            result_status['message'] = f"Обработка за {date_str} завершена. Отчет сохранен: {output_filename}"
            
            # Загрузка на Google Drive
            # Имя файла на диске будет таким же, как локальное (Отчет_ДАТА.xlsx)
            drive_filename = os.path.basename(output_filename) 
            logging.info(f"Запуск загрузки файла {output_filename} на Google Drive как '{drive_filename}'...")
            try:
                loop = asyncio.get_running_loop()
                # Передаем локальный путь и имя файла для диска
                await loop.run_in_executor(None, upload_to_drive, output_filename, drive_filename)
                logging.info(f"Загрузка файла на Google Drive инициирована.")
            except Exception as e:
                 logging.error(f"Ошибка при попытке запуска загрузки на Google Drive: {e}")
                 # Не меняем статус успеха, т.к. основная обработка прошла
                 result_status['message'] += " (Ошибка при загрузке на Google Drive)"
        else:
             logging.warning("Файл отчета пуст или не создан после обработки LLM.")
             result_status['message'] = f"Обработка за {date_str} завершена, но файл отчета не создан."
    else:
        logging.error(f"Асинхронная пакетная обработка сообщений за {date_str} завершилась с ошибкой.")
        result_status['message'] = f"Ошибка при LLM обработке сообщений за {date_str}."

    logging.info(f"--- Завершение обработки для даты: {date_str} ---")
    return result_status

# Старая функция main остается для возможности запуска из командной строки (обрабатывает всё)
async def main():
    logging.info(f"Проверка базы данных на наличие ВСЕХ необработанных сообщений: {DB_PATH}...")
    # Вызываем без даты для обработки всех
    unprocessed_messages = get_unprocessed_messages()

    if not unprocessed_messages:
        logging.info("Нет новых сообщений для обработки.")
        return

    message_texts = [msg[1] for msg in unprocessed_messages]
    message_ids = [msg[0] for msg in unprocessed_messages]

    # Используем базовое имя файла из config
    output_file = REPORT_OUTPUT_PATH
    logging.info(f"Запуск асинхронной обработки {len(message_texts)} сообщений. Результат будет сохранен в {output_file}")

    processed_data_list = await process_batch_async(
        messages=message_texts, 
        output_filename=output_file, 
        run_quality_test=False 
    )

    if processed_data_list is not None:
        logging.info(f"Асинхронная пакетная обработка ВСЕХ сообщений завершена. Получено {len(processed_data_list) if isinstance(processed_data_list, list) else 'N/A'} записей.")
        mark_messages_as_processed(message_ids)
        report_created = os.path.exists(output_file) and os.path.getsize(output_file) > 0
        if report_created:
            logging.info(f"Файл отчета {output_file} создан/обновлен.")
            logging.info(f"Запуск загрузки файла {output_file} на Google Drive...")
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, upload_to_drive, output_file)
            except Exception as e:
                 logging.error(f"Ошибка при попытке запуска загрузки на Google Drive: {e}")
        else:
             logging.warning("Файл отчета пуст или не создан, загрузка на Google Drive отменена.")
    else:
        logging.error("Асинхронная пакетная обработка ВСЕХ сообщений завершилась с ошибкой.")

if __name__ == "__main__":
    # Запуск обработки для конкретной даты (пример)
    # asyncio.run(run_processing_for_date('2025-04-18'))
    
    # Или запуск обработки всех необработанных сообщений (как раньше)
    asyncio.run(main())

