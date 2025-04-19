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

## Развёртывание DeepSeek‑LLM через Docker + Ollama (Локальный LLM)

Если вы хотите использовать модель DeepSeek локально на своем сервере вместо облачного API (например, OpenAI), вот инструкция по развертыванию с помощью Docker и Ollama. Это позволяет работать в том числе и в полностью изолированном сетевом контуре.

**Требования:**
*   Docker ≥ 20.10
*   `docker-compose` v2
*   Сервер с GPU: ≥ 48 ГБ VRAM для модели `deepseek-llm:67b-chat-q4_0` (вес ≈ 38 ГБ). Для моделей меньшего размера требования ниже.

---

### 📦 1. Быстрый онлайн-старт (требуется интернет для скачивания модели)

1.  **Скачайте `docker-compose.yml`:**
    Этот файл настроит Ollama и веб-интерфейс OpenWebUI.
    ```bash
    curl -L -o docker-compose.yml https://raw.githubusercontent.com/maxmcoding/deepseek-docker/main/docker-compose.yml
    # Или скачайте вручную: https://raw.githubusercontent.com/maxmcoding/deepseek-docker/main/docker-compose.yml
    ```

2.  **Поднимите стек:**
    Запускает контейнеры Ollama и OpenWebUI в фоновом режиме.
    ```bash
    docker compose up -d
    ```

3.  **Скачайте модель DeepSeek внутри контейнера:**
    Замените `deepseek-llm:67b-chat-q4_0` на нужную вам модель/версию из [библиотеки Ollama](https://ollama.com/library).
    ```bash
    docker exec -it ollamadeepseek ollama pull deepseek-llm:67b-chat-q4_0
    ```

    *   **API Endpoint:** `http://<SERVER_IP>:11434`
    *   **Web UI:** `http://<SERVER_IP>:8333` (OpenWebUI)

---

### 🔒 2. Полный офлайн-контур (для серверов без доступа в интернет)

1.  **На машине с доступом в интернет:**
    *   Установите Ollama локально ([инструкция](https://ollama.com/)).
    *   Скачайте нужную модель:
        ```bash
        ollama pull deepseek-llm:67b-chat-q4_0
        ```
    *   Экспортируйте модель в бандл:
        ```bash
        # Название бандла может быть любым
        ollama export deepseek-llm:67b-chat-q4_0 > deepseek-67b-q4.ollamabundle
        ```
        *Примечание: Размер файла `.ollamabundle` будет равен размеру модели (например, ~38 ГБ для 67B Q4).*

2.  **Перенесите файл `.ollamabundle`** на целевой сервер во внутреннем контуре (например, с помощью USB-накопителя).

3.  **На сервере без доступа в интернет:**
    *   Убедитесь, что Docker и docker-compose установлены.
    *   Скачайте или перенесите файл `docker-compose.yml` (см. шаг 1 онлайн-старта).
    *   **Отредактируйте `docker-compose.yml`**, чтобы Ollama использовал локальное хранилище моделей и не пытался ничего скачивать:
        ```yaml
        services:
          ollamadeepseek:
            # ... другие настройки ...
            volumes:
              - ./ollama_models:/root/.ollama  # Создайте папку ollama_models рядом с compose-файлом
            environment:
              - OLLAMA_MODELS=/root/.ollama
            # ... остальные настройки ...
        ```
    *   **Импортируйте модель из бандла:**
        Эта команда поместит модель в каталог, который будет подключен к контейнеру.
        ```bash
        # Создайте папку для моделей, если ее нет
        mkdir -p ./ollama_models
        # Запустите временный контейнер Ollama для импорта
        docker run --rm -v ./ollama_models:/root/.ollama -v ./deepseek-67b-q4.ollamabundle:/tmp/model.bundle ollama/ollama ollama import /tmp/model.bundle
        # Убедитесь, что модель появилась в ./ollama_models/manifests/registry.ollama.ai/library/deepseek-llm/
        ```
        *Примечание: Команда `ollama import` может потребовать установки Ollama на хосте или использования временного контейнера, как показано выше.*
    *   **Запустите сервис:**
        ```bash
        docker compose up -d
        ```
        Ollama теперь будет использовать только локально импортированные модели.

---

### ✅ 3. Быстрая проверка работы API

Выполните команду с сервера, где запущен Docker, или с другого хоста, имеющего доступ к `SERVER_IP`:
```bash
curl http://localhost:11434/api/generate \
  -d '{ "model": "deepseek-llm:67b-chat-q4_0", "prompt": "Привет, мир!", "stream": false }'
```
*Замените `localhost` на IP-адрес сервера, если проверяете с другой машины. Замените имя модели на то, которое вы скачали/импортировали.*

Если в ответ пришел JSON с результатом генерации — модель работает корректно.

---

### 💡 Интеграция с вашим проектом

Чтобы ваше Python-приложение (`app/main.py`, `app/llm_integration/`) использовало локально развернутый DeepSeek вместо OpenAI:

1.  **Измените конфигурацию LLM:**
    В файле `app/config.py` или через переменные окружения (`.env`) укажите параметры подключения к вашему Ollama API:
    *   `LLM_PROVIDER = "ollama"` (или другое значение, которое будет обрабатываться в `get_llm_client`)
    *   `OPENAI_API_BASE` (или `OLLAMA_API_BASE`) = `http://<SERVER_IP>:11434` (URL вашего Ollama сервера)
    *   `OPENAI_MODEL_NAME` (или `OLLAMA_MODEL_NAME`) = `deepseek-llm:67b-chat-q4_0` (имя модели, которую вы используете в Ollama)
    *   `OPENAI_API_KEY` (или `OLLAMA_API_KEY`) = `"ollama"` (или любое другое непустое значение, т.к. Ollama по умолчанию не требует ключ)

2.  **Адаптируйте код интеграции:**
    В файле `app/llm_integration/llm_client.py` (или где у вас создается клиент LLM) добавьте логику для инициализации клиента, совместимого с Ollama API (например, используя библиотеку `openai` версии >= 1.0, которая позволяет указывать `base_url` и `api_key`).

    ```python
    # Пример адаптации в llm_client.py
    from openai import OpenAI
    from app.config import settings

    def get_llm_client():
        if settings.LLM_PROVIDER == "ollama":
            return OpenAI(
                base_url=settings.OLLAMA_API_BASE, # Убедитесь, что эта переменная есть в config.py/settings
                api_key=settings.OLLAMA_API_KEY or 'ollama' # Ключ для Ollama обычно не важен
            )
        elif settings.LLM_PROVIDER == "openai":
            return OpenAI(api_key=settings.OPENAI_API_KEY)
        # Добавьте другие провайдеры при необходимости
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    def get_model_name():
         if settings.LLM_PROVIDER == "ollama":
             return settings.OLLAMA_MODEL_NAME # Убедитесь, что эта переменная есть
         elif settings.LLM_PROVIDER == "openai":
             return settings.OPENAI_MODEL_NAME
         else:
             # По умолчанию или ошибка
             return settings.OPENAI_MODEL_NAME

    # ... остальной код ...

    async def process_text_with_llm(text: str) -> Dict[str, Any]:
        client = get_llm_client()
        model_name = get_model_name()
        # ... ваш промпт и логика вызова ...
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                     {"role": "system", "content": "Ты - помощник для извлечения структурированной информации."},
                     {"role": "user", "content": f"Извлеки данные из следующего сообщения: {text}"} # Адаптируйте промпт
                 ],
                 # Доп. параметры, если нужно (temperature, max_tokens и т.д.)
            )
            # Обработайте ответ response.choices[0].message.content
            # ...
        except Exception as e:
            print(f"Ошибка при вызове LLM: {e}")
            # Обработка ошибки
        # ...
    ```
    *Не забудьте добавить соответствующие переменные (`OLLAMA_API_BASE`, `OLLAMA_API_KEY`, `OLLAMA_MODEL_NAME`, `LLM_PROVIDER`) в ваш `config.py` и `.env.example` / `.env`.*

## База данных

*   Сообщения хранятся в `app/parser/messages.db` (SQLite).
*   Таблица `messages` (создается `app/parser/db.js`) содержит колонки `id` (хеш сообщения), `source` (источник, например, имя чата), `text` (текст сообщения), `timestamp` (время получения) и `processed_at` (время обработки LLM).
*   Python-скрипт `app/main.py` выбирает сообщения, где `processed_at IS NULL`, и обновляет это поле после успешной обработки.

## Отчеты

*   Результаты обработки Python-скриптом сохраняются в папку `data/reports/`.
*   Имя файла для отчета за конкретную дату (при запуске из GUI или через `run_processing_for_date`) формируется как `Отчет_YYYY-MM-DD.xlsx`.
*   Созданные отчеты загружаются в папку Google Drive, указанную в GUI или через переменную окружения `GOOGLE_DRIVE_FOLDER_URL`. 