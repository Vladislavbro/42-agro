import pandas as pd
import os
import json
import datetime
import logging
import shutil

def calculate_comparison_metrics(benchmark_file_path: str, processing_file_path: str) -> dict | None:
    """
    Сравнивает два Excel файла и возвращает словарь с метриками и количеством строк.
    Возвращает None в случае критической ошибки чтения файлов.
    """
    # Инициализация словаря для возврата
    results = {
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0,
        "total_benchmark_rows": 0,
        "total_processing_rows": 0,
        "common_rows": 0,
        "unique_benchmark_rows": 0,
        "unique_processing_rows": 0,
        "error": None # Добавим поле для описания причины нулевых метрик
    }

    # Загрузка файлов
    try:
        benchmark_df = pd.read_excel(benchmark_file_path)
        processing_df = pd.read_excel(processing_file_path)
    except FileNotFoundError as e:
        msg = f"Не удалось найти файл для сравнения: {e.filename}."
        logging.warning(msg)
        results["error"] = msg
        return results # Возвращаем результаты с ошибкой
    except Exception as e:
        msg = f"Ошибка при чтении Excel файлов ({benchmark_file_path}, {processing_file_path}): {e}."
        logging.error(msg)
        results["error"] = msg
        return results # Возвращаем результаты с ошибкой

    # Удаление полностью пустых строк
    benchmark_df = benchmark_df.dropna(how='all')
    processing_df = processing_df.dropna(how='all')

    # Сохраняем количество строк *до* фильтрации по колонкам
    total_benchmark_initial = len(benchmark_df)
    total_processing_initial = len(processing_df)
    results["total_benchmark_rows"] = total_benchmark_initial
    results["total_processing_rows"] = total_processing_initial

    # Если после очистки датафреймы пусты
    if benchmark_df.empty and processing_df.empty:
        msg = "Оба файла пусты после очистки."
        logging.info(f"{msg} Считаем идеальным совпадением.")
        results.update({"precision": 1.0, "recall": 1.0, "f1_score": 1.0, "error": msg})
        # Строки остаются 0, так как они были пустыми
        return results
    if benchmark_df.empty or processing_df.empty:
        msg = f"Один из файлов пуст после очистки (Benchmark: {benchmark_df.empty}, Processing: {processing_df.empty})."
        logging.warning(f"{msg} Возвращаем нулевые метрики.")
        results["error"] = msg
        return results

    # Удаление колонки "дата", если она есть
    benchmark_df = benchmark_df.drop(columns=['Дата'], errors='ignore')
    processing_df = processing_df.drop(columns=['Дата'], errors='ignore')

    # Приведение к единому виду: сортировка колонок и строк
    common_cols = list(set(benchmark_df.columns) & set(processing_df.columns))
    if not common_cols:
        msg = "Нет общих колонок для сравнения между файлами."
        logging.warning(f"{msg} Возвращаем нулевые метрики.")
        results["error"] = msg
        return results

    benchmark_df = benchmark_df[common_cols].sort_index(axis=1).reset_index(drop=True)
    processing_df = processing_df[common_cols].sort_index(axis=1).reset_index(drop=True)

    # Обновляем кол-во строк после фильтрации по колонкам, если нужно (хотя обычно reset_index сохраняет кол-во)
    # results["total_benchmark_rows"] = len(benchmark_df)
    # results["total_processing_rows"] = len(processing_df)

    # Используем merge с indicator=True, чтобы найти уникальные строки
    try:
        merged_df = pd.merge(benchmark_df, processing_df, how='outer', indicator=True)
    except Exception as e:
        msg = f"Ошибка при объединении датафреймов: {e}."
        logging.error(f"{msg} Попробуйте проверить файлы. Возвращаем нулевые метрики.")
        results["error"] = msg
        return results

    num_common = len(merged_df[merged_df['_merge'] == 'both'])
    unique_benchmark = len(merged_df[merged_df['_merge'] == 'left_only'])
    unique_processing = len(merged_df[merged_df['_merge'] == 'right_only'])

    results["common_rows"] = num_common
    results["unique_benchmark_rows"] = unique_benchmark
    results["unique_processing_rows"] = unique_processing

    # Расчет F1-меры
    TP = num_common
    FP = unique_processing
    FN = unique_benchmark

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    results["precision"] = precision
    results["recall"] = recall
    results["f1_score"] = f1_score

    if f1_score == 0.0 and results["error"] is None:
         results["error"] = "F1 score is 0.0, likely due to no common rows found after cleaning and merging."

    return results


def save_quality_test_results(benchmark_file_path: str,
                              processing_file_path: str,
                              output_dir_base: str,
                              prompt_text: str,
                              llm_settings: dict,
                              provider_name: str):
    """
    Запускает тест сравнения, создает поддиректорию с провайдером и F1-скором в названии (провайдер-f1-X,XX)
    и сохраняет промпт (в .py), настройки LLM и детальные метрики (в одном .json) и копию файла с результатами (.xlsx).
    """
    logging.info(f"Запуск теста качества для '{os.path.basename(processing_file_path)}' относительно '{os.path.basename(benchmark_file_path)}'")

    metrics_result = calculate_comparison_metrics(benchmark_file_path, processing_file_path)

    if metrics_result is None:
        logging.error("Не удалось рассчитать метрики качества из-за ошибки чтения файлов.")
        return None

    f1_score = metrics_result["f1_score"]

    # Создание имени поддиректории (формат провайдер-f1-X,XX)
    f1_str_comma = f"{f1_score:.2f}".replace('.', ',')
    subdir_name = f"{provider_name}-f1-{f1_str_comma}"
    output_subdir = os.path.join(output_dir_base, subdir_name)

    try:
        # Создаем директорию. Если уже существует, она будет перезаписана новыми файлами.
        os.makedirs(output_subdir, exist_ok=True)
        logging.info(f"Создана/определена директория для результатов теста: {output_subdir}")

        # 1. Сохранение промпта в .py файл
        prompt_file_path = os.path.join(output_subdir, "prompt_snapshot.py")
        prompt_content = f'''# -*- coding: utf-8 -*-
PROMPT_TEXT = """{prompt_text}"""'''
        with open(prompt_file_path, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        logging.info(f"Промпт сохранен в: {prompt_file_path}")

        # 2. Подготовка данных для JSON
        serializable_settings = {k: str(v) if not isinstance(v, (str, int, float, bool, list, dict, type(None))) else v for k, v in llm_settings.items()}

        # Добавляем имена файлов в словарь метрик для полноты
        metrics_result["benchmark_file"] = os.path.basename(benchmark_file_path)
        metrics_result["processing_file"] = os.path.basename(processing_file_path)

        # Объединяем метрики и настройки
        results_data = {
            "metrics": metrics_result,
            "llm_settings": serializable_settings
        }

        # 3. Сохранение объединенного JSON
        results_file_path = os.path.join(output_subdir, "results.json")
        with open(results_file_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=4, ensure_ascii=False)
        logging.info(f"Метрики и настройки LLM сохранены в: {results_file_path}")

        # 3. Копирование файла с результатами (Excel)
        excel_dest_filename = f"{subdir_name}.xlsx"
        excel_dest_path = os.path.join(output_subdir, excel_dest_filename)
        try:
            shutil.copy2(processing_file_path, excel_dest_path)
            logging.info(f"Файл с результатами скопирован в: {excel_dest_path}")
        except Exception as copy_exc:
            logging.error(f"Не удалось скопировать файл {processing_file_path} в {excel_dest_path}: {copy_exc}")
            # Не прерываем выполнение, если копирование не удалось, но логируем ошибку

        logging.info(f"Результаты теста качества успешно сохранены в {output_subdir}")
        return output_subdir

    except Exception as e:
        logging.error(f"Ошибка при сохранении результатов теста качества в {output_subdir}: {e}")
        return None


# Основная часть скрипта (остается для возможности прямого запуска теста)
if __name__ == "__main__":
    # Импортируем config здесь, чтобы избежать циклических зависимостей при импорте utils в других местах
    try:
        from app import config
    except ImportError:
        # Попытка импорта для случаев, когда структура не app.*
        try:
            import config
        except ImportError:
            config = None # Не удалось импортировать конфиг
            logging.error("Не удалось импортировать файл конфигурации config.py при прямом запуске quality_test.py")
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))

    reports_dir_test = os.path.join(project_root, "data", "reports")
    benchmark_file_test = os.path.join(reports_dir_test, "benchmark-report.xlsx")
    processing_file_test = os.path.join(reports_dir_test, "processing_results.xlsx")
    
    # Определяем базовую директорию для тестов ИЗ КОНФИГА
    default_quality_test_dir = os.path.join(project_root, "data", "llm_quality_test")
    if config:
         quality_tests_dir = getattr(config, 'QUALITY_TEST_DIR', default_quality_test_dir)
    else:
         quality_tests_dir = default_quality_test_dir
         logging.warning(f"Используется путь по умолчанию для сохранения тестов: {quality_tests_dir}")

    os.makedirs(quality_tests_dir, exist_ok=True)

    dummy_prompt = "Это тестовый промпт для __main__."
    dummy_llm_settings = {"model": "test_model_main", "temperature": 0.1}

    if os.path.exists(benchmark_file_test) and os.path.exists(processing_file_test):
        metrics_dict = calculate_comparison_metrics(benchmark_file_test, processing_file_test)
        print(f"--- Результат calculate_comparison_metrics ---")
        if metrics_dict:
            print(json.dumps(metrics_dict, indent=4, ensure_ascii=False))
        else:
             print("Функция calculate_comparison_metrics вернула None")
        print("---")

        if metrics_dict: 
            saved_path = save_quality_test_results(
                benchmark_file_path=benchmark_file_test,
                processing_file_path=processing_file_test,
                output_dir_base=quality_tests_dir,
                prompt_text=dummy_prompt,
                llm_settings=dummy_llm_settings,
                provider_name="manual_test"
            )
            if saved_path:
                print(f"Результаты теста сохранены в: {saved_path}")
            else:
                print("Не удалось сохранить результаты теста.")
        else:
            print("Пропускаем сохранение результатов, так как метрики не были рассчитаны.")
    else:
        print("Не найдены файлы benchmark-report.xlsx или processing_results.xlsx в data/reports для запуска теста.")