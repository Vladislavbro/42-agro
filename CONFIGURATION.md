# Руководство по настройке

Этот файл описывает, где и как настраивать ключевые параметры приложения.

## 1. Настройки Парсера (Node.js)

Эти настройки изменяются непосредственно в коде парсера.

### 1.1. Источники сообщений WhatsApp

*   **Что:** Указывает, из каких личных чатов и групп WhatsApp собирать сообщения.
*   **Где:** Файл `app/parser/index.js`
*   **Переменные:** 
    *   `TARGET_WHATSAPP_CHATS`: Массив строк с **точными именами** личных чатов.
    *   `TARGET_WHATSAPP_GROUPS`: Массив строк с **точными именами** групп.
*   **Пример:**
    ```javascript
    const TARGET_WHATSAPP_CHATS = ['Иван Петров'];
    const TARGET_WHATSAPP_GROUPS = ['Отчеты механизаторов', 'Полевые работы'];
    ```

### 1.2. Источники сообщений Telegram (если используется)

*   **Что:** Указывает API-ключи Telegram и целевые чаты/группы.
*   **Где:** Файл `app/parser/index.js`
*   **Переменные:**
    *   `API_ID`: Ваш API ID от Telegram (число).
    *   `API_HASH`: Ваш API Hash от Telegram (строка).
    *   `TARGET_TELEGRAM_USERNAMES`: Массив строк с юзернеймами пользователей Telegram.
    *   `TARGET_TELEGRAM_GROUPS`: Массив строк с **точными названиями** групп Telegram.
*   **Пример:**
    ```javascript
    const API_ID = 1234567;
    const API_HASH = "abcdef12345...";
    const TARGET_TELEGRAM_USERNAMES = ['ivan_petrov_tg'];
    const TARGET_TELEGRAM_GROUPS = ['Агро Группа TG'];
    ```

### 1.3. Папка Google Drive для `.docx` файлов

*   **Что:** Указывает папку на Google Диске, куда парсер будет сохранять `.docx` копии сообщений.
*   **Где:** Файл `app/parser/driveUploader.js`
*   **Переменная:** `PARENT_FOLDER_ID`
*   **Как настроить:** Заменить значение константы на **ID** нужной папки Google Диска (ID можно найти в URL папки).
*   **Пример:**
    ```javascript
    // ID папки взят из URL: https://drive.google.com/drive/folders/ВАШ_ID_ПАПКИ
    const PARENT_FOLDER_ID = 'ВАШ_ID_ПАПКИ'; 
    ```

## 2. Настройки Python-части (Обработка LLM и загрузка отчетов)

Эти настройки задаются через файл `.env` в корневой директории проекта.

### 2.1. Папка Google Drive для Excel-отчетов

*   **Что:** Указывает папку на Google Диске, куда будет загружаться итоговый Excel-отчет (`Отчет_{дата}.xlsx`), созданный после LLM-обработки.
*   **Где:** Файл `.env` (в корне проекта)
*   **Переменная:** `GOOGLE_DRIVE_FOLDER_URL`
*   **Как настроить:** Указать **полную ссылку (URL)** на папку Google Диска.
*   **Пример:**
    ```dotenv
    GOOGLE_DRIVE_FOLDER_URL="https://drive.google.com/drive/folders/ВАШ_ID_ПАПКИ"
    ```

### 2.2. Настройки LLM и другие

*   Другие настройки (API ключи LLM, выбор провайдера и т.д.) также находятся в файле `.env`. См. комментарии в самом файле или в `app/config.py` для деталей. 