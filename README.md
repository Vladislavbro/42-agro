# Проект обработки сообщений Agro

Этот проект предназначен для автоматической обработки текстовых сообщений из WhatsApp (и потенциально Telegram), извлечения из них структурированной информации с помощью LLM и сохранения результатов в формате Excel с последующей загрузкой на Google Drive. Проект включает в себя Node.js парсер для сбора сообщений, Python бэкенд для их обработки и графический интерфейс (GUI) на Tkinter для управления процессом.

## Основные компоненты

*   **Парсер WhatsApp/Telegram:** (Node.js приложение в `app/parser/`)
    *   Подключается к WhatsApp с использованием `whatsapp-web.js` (требует сканирования QR-кода при первом запуске).
    *   Сохраняет сообщения из указанного чата/группы WhatsApp в базу данных SQLite (`app/parser/messages.db`).
    *   *Примечание:* Также содержит код для интеграции с Telegram, который может быть активен или закомментирован (`index.js`).
    *   Запускается из графического интерфейса или может быть запущен отдельно.
*   **Обработчик LLM:** (Python, `app/llm_integration/`)
    *   Использует языковую модель (например, OpenAI GPT) для анализа текстов сообщений, полученных из базы данных.
    *   Извлекает структурированную информацию согласно заданным правилам/промптам.
*   **Основной скрипт обработки:** (Python, `app/main.py`)
    *   Получает необработанные сообщения из БД SQLite.
    *   Вызывает обработчик LLM для анализа сообщений.
    *   Сохраняет результаты в Excel-файл (`data/reports/Отчет_ДАТА.xlsx`).
    *   Помечает сообщения как обработанные в базе данных.
    *   Загружает созданный отчет в указанную папку Google Drive (`app/utils/google_drive_uploader.py`).
    *   Вызывается из графического интерфейса.
*   **Графический интерфейс (GUI):** (Python/Tkinter, `app/gui/main_window.py`)
    *   Предоставляет пользователю возможность выбрать дату для обработки.
    *   Позволяет указать URL папки Google Drive для загрузки отчета.
    *   Позволяет указать точное название чата или группы WhatsApp для сбора сообщений.
    *   Запускает/останавливает Node.js парсер.
    *   Инициирует процесс обработки сообщений через `app/main.py`.
    *   Отображает результаты обработки (содержимое Excel-отчета) в таблице.
    *   Позволяет сохранить полученный Excel-отчет локально.
*   **Конфигурация:** (`app/config.py`, `.env`) Содержит настройки Python-части: пути к файлам, ключи API и т.д.
*   **База данных:** (`app/parser/messages.db`) SQLite база данных для хранения сообщений и их статуса обработки. Создается и управляется Node.js парсером.

## Установка

1.  **Клонируйте репозиторий:**
    ```bash
    git clone <URL вашего репозитория>
    cd <имя папки репозитория>
    ```

2.  **Установите Node.js:** Если у вас не установлен Node.js (включая npm), скачайте и установите его с [официального сайта](https://nodejs.org/).

3.  **Установите зависимости парсера (Node.js):**
    Перейдите в директорию парсера и установите зависимости:
    ```bash
    cd app/parser
    npm install
    cd ../..  # Вернуться в корневую директорию проекта
    ```

4.  **Создайте и активируйте виртуальное окружение Python** (рекомендуется):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Для Linux/macOS
    # или
    .venv\\Scripts\\activate  # Для Windows
    ```

5.  **Установите зависимости Python:**
    ```bash
    pip install -r requirements.txt
    ```

6.  **Настройте переменные окружения:**
    *   Скопируйте файл `.env.example` в `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Отредактируйте файл `.env` и заполните необходимые значения:
        *   `OPENAI_API_KEY`: Ваш ключ API от OpenAI (или другого LLM-провайдера).
        *   `GOOGLE_DRIVE_FOLDER_URL`: URL папки на Google Drive, куда будут загружаться отчеты (это значение можно будет также ввести в GUI).

7.  **Настройте доступ к Google API (Drive):**
    *   Создайте проект в Google Cloud Console, включите Google Drive API.
    *   Создайте учетные данные типа "OAuth client ID" (тип "Desktop application").
    *   Скачайте JSON-файл с учетными данными и переименуйте его в `credentials.json`. Поместите этот файл в директорию `app/parser/`.
    *   При первом запуске парсера (или загрузки на Drive) может потребоваться пройти аутентификацию через браузер. Сгенерированный токен (`token.json`) будет сохранен в `app/parser/` для последующих запусков.
    *   Убедитесь, что `.gitignore` настроен так, чтобы не добавлять секретные файлы (`.env`, `credentials.json`, `token.json`, `telegram.session`, папки `session`, `.wwebjs_cache`) в репозиторий. *Текущий `.gitignore` выглядит подходящим.*

## Запуск

Основной способ запуска - через графический интерфейс.

1.  **Запустите GUI:**
    Убедитесь, что ваше виртуальное окружение Python активировано. Перейдите в корневую директорию проекта и выполните:
    ```bash
    python -m app.gui.main_window
    ```

2.  **Работа с GUI:**
    *   **При первом запуске WhatsApp парсера:** В терминале, из которого вы запустили GUI, появится QR-код. Отсканируйте его с помощью приложения WhatsApp на вашем телефоне (Связанные устройства -> Привязка устройства). После успешного сканирования парсер будет готов к работе. Сессия сохранится в папке `app/parser/session`.
    *   **Введите URL папки Google Drive:** Укажите полный URL папки на Google Drive, куда будут сохраняться отчеты.
    *   **Введите название чата/группы WhatsApp:** Укажите точное имя чата или группы WhatsApp, сообщения из которой нужно обрабатывать.
    *   **Выберите дату:** Выберите дату, за которую хотите обработать сообщения.
    *   **Нажмите "Запустить обработку":**
        *   GUI запустит Node.js парсер (если он еще не запущен). Парсер начнет слушать/собирать сообщения из указанного WhatsApp чата за выбранный день и сохранять их в БД. *Примечание: GUI удаляет старую БД `messages.db` перед запуском парсера.*
        *   Через 60 секунд (время для сбора сообщений) GUI запустит Python-скрипт `app/main.py` для обработки собранных сообщений за выбранную дату.
        *   Ход процесса (Сбор сообщений, Обработка LLM) будет отображаться в заголовке окна.
        *   По завершении появится сообщение об успехе или ошибке.
        *   Если обработка прошла успешно и отчет создан, его содержимое будет отображено в таблице. Отчет также будет загружен на Google Drive.
    *   **Кнопка "Сохранить Excel":** Становится активной после успешного создания и отображения отчета. Позволяет сохранить копию Excel-файла локально.
    *   **Закрытие окна GUI:** При закрытии окна автоматически останавливается запущенный Node.js парсер.

3.  **Запуск компонентов по отдельности (для отладки):**
    *   **Парсер:**
        ```bash
        cd app/parser
        # Передайте URL папки Drive и название чата/группы как аргументы
        node index.js "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" "Название вашего чата WhatsApp"
        cd ../..
        ```
    *   **Основной скрипт обработки (Python):**
        Обрабатывает *все* необработанные сообщения из БД и загружает *общий* отчет (`agro_report.xlsx`) на Google Drive (требует настройки URL в `upload_to_drive` внутри `main()` или использования `run_processing_for_date`).
        ```bash
        python -m app.main
        ```
        Или для конкретной даты (пример):
        ```python
        # Создайте отдельный скрипт или выполните в Python-консоли
        import asyncio
        import os
        from dotenv import load_dotenv
        from app.main import run_processing_for_date
        load_dotenv()
        google_drive_folder_url = os.getenv('GOOGLE_DRIVE_FOLDER_URL')
        if google_drive_folder_url:
            asyncio.run(run_processing_for_date('2024-05-21', google_drive_folder_url))
        else:
            print("Установите GOOGLE_DRIVE_FOLDER_URL в .env")
        ```

## База данных

*   Сообщения хранятся в `app/parser/messages.db` (SQLite).
*   Таблица `messages` (создается `app/parser/db.js`) содержит колонки `id` (хеш сообщения), `source` (источник, например, имя чата), `text` (текст сообщения), `timestamp` (время получения) и `processed_at` (время обработки LLM).
*   Python-скрипт `app/main.py` выбирает сообщения, где `processed_at IS NULL`, и обновляет это поле после успешной обработки.
*   GUI удаляет файл `messages.db` перед каждым запуском обработки через кнопку "Запустить обработку".

## Отчеты

*   Результаты обработки Python-скриптом сохраняются в папку `data/reports/`.
*   Имя файла для отчета за конкретную дату (при запуске из GUI или через `run_processing_for_date`) формируется как `Отчет_YYYY-MM-DD.xlsx`.
*   Созданные отчеты загружаются в папку Google Drive, указанную в GUI или через переменную окружения `GOOGLE_DRIVE_FOLDER_URL`. 