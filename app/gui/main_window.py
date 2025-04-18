import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
# from app.gui.mock_api import mock_send_messages_request, mock_get_reports, mock_save_excel # Удаляем моки

# --- Новые импорты ---
import threading
import queue
import pandas as pd
import shutil
import os
import asyncio
import logging
from app.main import run_processing_for_date # Импортируем функцию бэкенда
from app.config import BASE_DIR # Нужен для построения пути к отчету по умолчанию
# --- Конец новых импортов ---

# --- Очередь для связи потоков ---
processing_queue = queue.Queue()
# Переменная для хранения пути к последнему успешному отчету
last_successful_report_path = None 
# --- Конец очереди ---


def on_load_messages():
    global last_successful_report_path
    selected_date = date_picker.get_date()
    date_str = selected_date.strftime('%Y-%m-%d') # Используем strftime для нужного формата

    # Очищаем таблицу перед запуском
    for row in report_table.get_children():
        report_table.delete(row)
    last_successful_report_path = None # Сбрасываем путь к отчету
    root.update_idletasks() # Обновляем GUI

    # Блокируем кнопку
    load_button.config(state=tk.DISABLED)
    root.title(f"Агро-отчёты - Обработка {date_str}...") # Индикатор в заголовке

    # Функция-обертка для запуска в потоке
    def processing_worker(date_to_process, result_queue):
        try:
            # Запускаем асинхронную функцию в текущем потоке с новым event loop
            result = asyncio.run(run_processing_for_date(date_to_process))
            result_queue.put(result)
        except Exception as e:
            # Отправляем информацию об ошибке через очередь
            result_queue.put({
                'success': False, 
                'message': f"Критическая ошибка в потоке обработки: {e}",
                'report_path': None,
                'processed_count': 0
            })

    # Запускаем поток
    thread = threading.Thread(target=processing_worker, args=(date_str, processing_queue))
    thread.start()

    # Начинаем проверку очереди
    check_processing_queue()

def check_processing_queue():
    """Проверяет очередь результатов из потока обработки."""
    global last_successful_report_path
    try:
        result = processing_queue.get_nowait() # Проверяем без блокировки

        # Обработка завершена, разблокируем кнопку и убираем индикатор
        load_button.config(state=tk.NORMAL)
        root.title("Агро-отчёты") 

        # Показываем сообщение о результате
        if result['success']:
            messagebox.showinfo("Завершено", result['message'])
        else:
            messagebox.showerror("Ошибка обработки", result['message'])
            return # Не пытаемся читать отчет при ошибке

        # Если успешно и есть путь к отчету, читаем и отображаем
        if result['success'] and result['report_path'] and os.path.exists(result['report_path']):
            try:
                last_successful_report_path = result['report_path'] # Сохраняем путь
                logging.info(f"Чтение данных из отчета: {last_successful_report_path}")
                df = pd.read_excel(last_successful_report_path)
                # Заменяем NaN на пустые строки для корректного отображения
                df = df.fillna('') 
                # Преобразуем DataFrame в список списков/кортежей для Treeview
                report_data_for_table = df.to_records(index=False).tolist()
                update_table(report_data_for_table) # Отправляем в таблицу
            except FileNotFoundError:
                messagebox.showerror("Ошибка", f"Файл отчета не найден: {result['report_path']}")
                last_successful_report_path = None
            except Exception as e:
                messagebox.showerror("Ошибка чтения отчета", f"Не удалось прочитать Excel файл: {e}")
                last_successful_report_path = None
        elif result['success']:
             # Обработка успешна, но отчет не создан (например, не было сообщений)
             # Просто очищаем таблицу (уже сделано в on_load_messages)
             logging.info("Отчет не был создан (вероятно, не было данных), таблица очищена.")
             last_successful_report_path = None

    except queue.Empty:
        # Очередь пуста, проверяем снова через 200 мс
        root.after(200, check_processing_queue)

def update_table(reports_data):
    # Очищаем старые строки (на всякий случай, хотя делаем это и в on_load_messages)
    for row in report_table.get_children():
        report_table.delete(row)

    # Добавляем новые строки из списка списков/кортежей
    for report_row in reports_data:
        # Убедимся, что передаем правильное количество значений
        # Если данные из pandas, они должны соответствовать колонкам
        report_table.insert("", "end", values=report_row)

def on_save_excel():
    global last_successful_report_path
    
    # Проверяем, есть ли путь к последнему успешному отчету
    if not last_successful_report_path or not os.path.exists(last_successful_report_path):
        messagebox.showwarning("Нет отчета", "Сначала нужно успешно загрузить и обработать сообщения.")
        return

    # Получаем дату из имени файла (для предложенного имени сохранения)
    try:
        # Пример имени: .../processing_results_2025-04-18.xlsx
        date_str = os.path.basename(last_successful_report_path).split('_')[-1].split('.')[0]
    except IndexError:
        date_str = "report" # Запасной вариант

    # Предлагаем имя файла для сохранения
    suggested_filename = f"report_{date_str}.xlsx"

    # Используем asksaveasfilename
    dest_path = filedialog.asksaveasfilename(
        title="Сохранить отчет Excel как...",
        initialfile=suggested_filename,
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
    )

    if not dest_path:
        return # Пользователь отменил выбор

    try:
        shutil.copyfile(last_successful_report_path, dest_path)
        messagebox.showinfo("Файл сохранён", f"Отчёт успешно сохранён как:\n{dest_path}")
    except Exception as e:
        messagebox.showerror("Ошибка сохранения", f"Не удалось скопировать файл отчета:\n{e}")


# Главное окно
root = tk.Tk()
root.title("Агро-отчёты")
root.geometry("950x500")
root.resizable(True, True)

# Верхняя панель с выбором даты
top_frame = ttk.Frame(root)
top_frame.pack(pady=10)

date_label = ttk.Label(top_frame, text="Выберите дату:")
date_label.pack(side="left", padx=5)

date_picker = DateEntry(top_frame, width=15, background="darkblue", foreground="white", date_pattern="yyyy-mm-dd")
date_picker.pack(side="left")

load_button = ttk.Button(top_frame, text="Загрузить сообщения", command=on_load_messages)
load_button.pack(side="left", padx=10)

# Таблица
columns = [
    "Дата", "Подразделение", "Операция", "Культура",
    "За день, га", "С начала операции, га", "Вал за день, ц", "Вал с начала, ц"
]

report_table = ttk.Treeview(root, columns=columns, show="headings", height=15)
for col in columns:
    report_table.heading(col, text=col)
    report_table.column(col, width=110, anchor="center")

report_table.pack(expand=True, fill="both", padx=10, pady=10)

# Скроллбар
scrollbar = ttk.Scrollbar(root, orient="vertical", command=report_table.yview)
report_table.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Нижняя панель с кнопкой сохранения
bottom_frame = ttk.Frame(root)
bottom_frame.pack(pady=5)

save_button = ttk.Button(bottom_frame, text="Сохранить в Excel", command=on_save_excel)
save_button.pack()

# Запуск
if __name__ == "__main__":
    # Запускаем главный цикл
    root.mainloop()
