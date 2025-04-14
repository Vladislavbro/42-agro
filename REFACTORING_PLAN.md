# План Сборки Проекта "Агро-Отчеты" (Обновленный)

Этот документ описывает план рефакторинга кода из Jupyter-ноутбука `notebooks/gemini-test.ipynb` в структуру проекта, описанную в `STRUCTURE.md`, с учетом использования DeepSeek API как основного и Gemini API как резервного (выбираемого через конфигурацию).

**Основной Стек:**

*   **Язык:** Python
*   **LLM:** DeepSeek (основной), Gemini (резервный)
*   **Хранение данных:** Google Sheets
*   **Обработка сообщений:** Пользовательский парсинг + LLM
*   **Окружение:** `.venv`, `requirements.txt`

**Текущий Статус (Выполненные Шаги):**

1.  **Созданы файлы справочников:**
    *   `data/mappings/cultures.txt`
    *   `data/mappings/operations.txt`
    *   `data/mappings/departments.json`
2.  **Обновлен `.env`:** Добавлены переменные для DeepSeek API (`DEEPSEEK_API_KEY`, `PRIMARY_LLM_PROVIDER`).
3.  **Создана структура каталогов:**
    *   `app/llm_integration/`
    *   Созданы пустые файлы: `app/llm_integration/__init__.py`, `client.py`, `prompt_builder.py`, `extractor.py`.

**План Рефакторинга (Следующие Шаги):**

1.  **`app/config.py`:**
    *   Реализовать загрузку переменных окружения из `.env` (API ключи, `PRIMARY_LLM_PROVIDER`, Google Sheets ID и credentials path).
    *   Добавить константы или функции для получения путей к файлам справочников в `data/mappings/`.

2.  **`app/llm_integration/prompt_builder.py`:**
    *   Создать функцию `load_mapping_file(file_path: str) -> str` для загрузки содержимого файлов справочников.
    *   Реализовать функцию `build_detailed_extraction_prompt(input_message: str, cultures_content: str, operations_content: str, departments_content: str, current_date: str) -> str`:
        *   Принимает текст сообщения и *содержимое* файлов справочников.
        *   Формирует полный текст промпта для извлечения всех записей (аналогично `extract_detailed_agro_reports` из ноутбука).
    *   Реализовать функцию `build_structure_analysis_prompt(input_message: str, cultures_content: str, operations_content: str, departments_content: str) -> str`:
        *   Принимает текст сообщения и *содержимое* файлов справочников.
        *   Формирует полный текст промпта для анализа структуры сообщения (аналогично `analyze_message_structure_with_gemini` из ноутбука).

3.  **`app/llm_integration/client.py`:**
    *   Импортировать необходимые библиотеки (`google.generativeai`, `openai` или специфичную для DeepSeek, `os`, конфигурацию из `app.config`).
    *   Создать класс или функции для инициализации LLM клиента:
        *   При инициализации читать `PRIMARY_LLM_PROVIDER` из конфига.
        *   В зависимости от провайдера, инициализировать *только* соответствующий клиент (DeepSeek или Gemini), используя API-ключ из конфига.
        *   Хранить активный клиент.
    *   Реализовать функцию `generate_response(prompt: str) -> str`:
        *   Принимает готовый текст промпта.
        *   Использует *активный* клиент для отправки запроса к LLM API.
        *   Обрабатывает возможные ошибки API.
        *   Возвращает текстовый ответ от LLM.

4.  **`app/llm_integration/extractor.py`:**
    *   Импортировать `json`.
    *   Реализовать функцию `extract_json_list(llm_response: str) -> list | None`:
        *   Принимает текстовый ответ от LLM.
        *   Пытается очистить ответ от возможных ```json ``` маркеров.
        *   Парсит строку как JSON-список.
        *   Обрабатывает ошибки `json.JSONDecodeError`.
        *   Возвращает список словарей или `None` при ошибке.
    *   Реализовать функцию `extract_json_object(llm_response: str) -> dict | None`:
        *   Аналогично `extract_json_list`, но парсит как JSON-объект (словарь).

5.  **`app/message_processing/` (`parser.py`, `validator.py`):**
    *   Создать эти файлы.
    *   Определить, нужна ли предварительная обработка/валидация сообщений *перед* отправкой в LLM. Если да, реализовать соответствующие функции (например, проверка наличия цифр, ключевых слов и т.д.). Пока можно оставить пустыми или с базовыми заглушками.

6.  **`app/google_sheets_integration/` (`client.py`, `writer.py`):**
    *   Создать эти файлы.
    *   `client.py`: Реализовать аутентификацию с Google Sheets API с использованием файла credentials (путь из `app/config.py`).
    *   `writer.py`: Реализовать функцию для добавления данных (списка словарей, полученных от LLM) в указанную Google Таблицу (ID из `app/config.py`).

7.  **`app/main.py`:**
    *   Создать файл.
    *   Реализовать основной поток выполнения:
        *   Загрузка конфигурации.
        *   Инициализация LLM клиента (`llm_integration.client`).
        *   Инициализация Google Sheets клиента (`google_sheets_integration.client`).
        *   (Цикл или функция для обработки одного сообщения)
            *   Получение входящего сообщения (пока можно читать из файла или строки).
            *   (Опционально) Вызов функций из `message_processing`.
            *   Загрузка содержимого справочников (`prompt_builder.load_mapping_file`).
            *   Построение промпта с помощью `prompt_builder.build_detailed_extraction_prompt`.
            *   Отправка запроса к LLM через `llm_integration.client.generate_response`.
            *   Извлечение JSON-списка из ответа с помощью `llm_integration.extractor.extract_json_list`.
            *   Запись извлеченных данных в Google Sheets с помощью `google_sheets_integration.writer`.
            *   Логирование результатов и ошибок.

8.  **`tests/`:**
    *   Создать структуру тестов, зеркальную `app/`.
    *   Написать юнит-тесты для функций в `prompt_builder`, `extractor`, `google_sheets_writer`.
    *   Написать интеграционные тесты (возможно, с использованием моков для внешних API) для `llm_integration.client` и основного потока в `app/main.py`.

9.  **`notebooks/gemini-test.ipynb`:**
    *   Удалить ячейки с кодом, который был перенесен в модули `app/`.
    *   Оставить ноутбук для экспериментов, возможно, добавить ячейки для вызова функций из новых модулей.

10. **`requirements.txt`:**
    *   Добавить все необходимые зависимости (`google-generativeai`, `openai` (для DeepSeek), `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`, `python-dotenv`). 