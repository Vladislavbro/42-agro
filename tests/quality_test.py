import pandas as pd
import os

# Определяем пути к файлам
reports_dir = "data/reports"
benchmark_file = os.path.join(reports_dir, "benchmark-report.xlsx")
processing_file = os.path.join(reports_dir, "processing_results.xlsx")

# Загрузка файлов
try:
    benchmark_df = pd.read_excel(benchmark_file)
    processing_df = pd.read_excel(processing_file)
except FileNotFoundError as e:
    print(f"Ошибка: Не найден файл {e.filename}")
    exit()

# Удаление полностью пустых строк
benchmark_df = benchmark_df.dropna(how='all')
processing_df = processing_df.dropna(how='all')

# Удаление колонки "дата", если она есть
benchmark_df = benchmark_df.drop(columns=['Дата'], errors='ignore')
processing_df = processing_df.drop(columns=['Дата'], errors='ignore')

# Приведение к единому виду: сортировка колонок и строк
# Сначала убедимся, что колонки одинаковые перед сортировкой по индексу
common_cols = list(set(benchmark_df.columns) & set(processing_df.columns))
benchmark_df = benchmark_df[common_cols].sort_index(axis=1).reset_index(drop=True)
processing_df = processing_df[common_cols].sort_index(axis=1).reset_index(drop=True)

# Получаем количество строк после очистки
total_benchmark = len(benchmark_df)
total_processing = len(processing_df)

# Подсчет одинаковых строк
# Используем merge с indicator=True, чтобы найти уникальные строки
merged_df = pd.merge(benchmark_df, processing_df, how='outer', indicator=True)

num_common = len(merged_df[merged_df['_merge'] == 'both'])
unique_benchmark = len(merged_df[merged_df['_merge'] == 'left_only'])
unique_processing = len(merged_df[merged_df['_merge'] == 'right_only'])


# Расчет F1-меры
# True Positives (TP) = num_common
# False Positives (FP) = unique_processing
# False Negatives (FN) = unique_benchmark
TP = num_common
FP = unique_processing
FN = unique_benchmark

precision = TP / (TP + FP) if (TP + FP) > 0 else 0
recall = TP / (TP + FN) if (TP + FN) > 0 else 0
f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0


# Вывод результата
print(f"--- Сравнение {os.path.basename(benchmark_file)} и {os.path.basename(processing_file)} ---")
print(f"Строк в benchmark (после очистки): {total_benchmark}")
print(f"Строк в processing (после очистки): {total_processing}")
print(f"Совпадающих строк: {num_common}")
print(f"Уникальных строк в benchmark: {unique_benchmark}")
print(f"Уникальных строк в processing: {unique_processing}")
print(f"F1-мера: {f1_score:.4f}")