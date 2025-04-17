import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from app.gui.mock_api import mock_send_messages_request, mock_get_reports, mock_save_excel

def on_load_messages():
    selected_date = date_picker.get_date()
    date_str = selected_date.isoformat()

    result = mock_send_messages_request(date_str)
    msg = f"Сообщений получено: {result['messages_received']}\nОтчётов извлечено: {result['reports_saved']}"
    messagebox.showinfo("Готово", msg)

    # Загружаем отчёты
    reports = mock_get_reports(date_str)
    update_table(reports)

def update_table(reports):
    # Очищаем старые строки
    for row in report_table.get_children():
        report_table.delete(row)

    # Добавляем новые
    for report in reports:
        values = [
            report.get("Дата"),
            report.get("Подразделение"),
            report.get("Операция"),
            report.get("Культура"),
            report.get("За день, га"),
            report.get("С начала операции, га"),
            report.get("Вал за день, ц"),
            report.get("Вал с начала, ц")
        ]
        report_table.insert("", "end", values=values)
def on_save_excel():
    selected_date = date_picker.get_date().isoformat()

    folder = filedialog.askdirectory(title="Выберите папку для сохранения Excel")
    if not folder:
        return  # пользователь отменил выбор

    try:
        path = mock_save_excel(selected_date, folder)
        messagebox.showinfo("Файл сохранён", f"Отчёт сохранён:\n{path}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")


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
    root.mainloop()
