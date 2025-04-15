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

1.  **`app/config.py`:** - **Готово**
    *   Реализована загрузка переменных окружения из `.env`.
    *   Добавлены константы для путей к файлам справочников.

2.  **`app/llm_integration/prompt_builder.py`:** - **Готово**
    *   Реализована функция `load_mapping_file(file_path: str) -> str`.
    *   Реализована функция `build_detailed_extraction_prompt(input_message: str, cultures_content: str, operations_content: str, departments_content: str, current_date: str) -> str`:
        *   Принимает текст сообщения и содержимое файлов справочников.
        *   Формирует полный текст промпта для извлечения всех записей.
    *   Функция `build_structure_analysis_prompt` на данный момент не требуется и удалена/закомментирована.

3.  **`app/llm_integration/client.py` (и связанные модули):** - **Готово**
    *   Импортированы необходимые библиотеки (`google.generativeai`, `openai`, `os`, конфигурация из `app.config`).
    *   Создан класс `TextGenerationClient` (`app/llm_integration/client.py`):
        *   При инициализации читает `PRIMARY_LLM_PROVIDER` из конфига.
        *   В зависимости от провайдера (deepseek/gemini), инициализирует соответствующий клиент, используя API-ключ из конфига.
        *   Хранит активный клиент и модель.
    *   Реализован метод `generate_response(prompt: str) -> str | None`:
        *   Принимает готовый текст промпта.
        *   Использует *активный* клиент для отправки запроса к LLM API (DeepSeek или Gemini).
        *   Логика для каждого провайдера вынесена в приватные методы (`_generate_deepseek_response`, `_generate_gemini_response`).
        *   Обрабатывает возможные ошибки API.
        *   Возвращает текстовый ответ от LLM или None.

3.1. **Добавлен клиент для OpenAI Schema Extraction:** - **Готово**
    *   Создан `app/llm_integration/constants.py`:
        *   Содержит константы `OPENAI_REPORT_SCHEMA` (JSON схема) и `OPENAI_SCHEMA_PROMPT` (шаблон промпта).
    *   Создан `app/llm_integration/openai_extractor.py`:
        *   Содержит класс `OpenAISchemaExtractor`.
        *   Инициализируется с клиентом `openai.OpenAI`.
        *   Реализован метод `extract_data(...)`, использующий OpenAI Responses API (`client.responses.create`) с передачей схемы в параметре `text`, для извлечения структурированных данных согласно `OPENAI_REPORT_SCHEMA`. (Этот клиент сам обрабатывает и парсит JSON ответ от OpenAI).

4.  **`app/llm_integration/extractor.py`:** - **Готово**
    *   Импортирован `json` и `logging`.
    *   Реализована функция `extract_json_list(llm_response: str) -> list | None`:
        *   Принимает текстовый ответ от LLM (полученный от `TextGenerationClient`).
        *   Пытается очистить ответ от возможных ```json ``` маркеров или другого лишнего текста.
        *   Парсит очищенную строку как JSON-список.
        *   Обрабатывает ошибки `json.JSONDecodeError`.
        *   Возвращает список словарей или `None` при ошибке.
    *   Реализован метод `extract_json_object(llm_response: str) -> dict | None`:
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