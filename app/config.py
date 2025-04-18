import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
# Ищем .env файл начиная с директории, где находится config.py, и поднимаясь выше
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') # Путь к .env в корне проекта
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path, override=True)
else:
    # Если .env не найден в корне, попробуем загрузить из текущей директории 
    # (на случай запуска скриптов не из корня)
    load_dotenv(override=True) 

# --- LLM Configuration ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE") # Добавляем загрузку base_url для DeepSeek
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Добавляем загрузку ключа OpenAI
PRIMARY_LLM_PROVIDER = os.getenv("PRIMARY_LLM_PROVIDER", "deepseek").lower() # По умолчанию deepseek

# --- Model Names --- (Загружаем из .env с дефолтами)
DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini") # Используем указанную модель
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2")) # Добавлена температура

# Настройки асинхронной обработки
MAX_CONCURRENT_REQUESTS = 1 # Максимальное количество одновременных запросов к LLM

# --- Google Sheets Configuration ---
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# GOOGLE_SHEET_RANGE = os.getenv("GOOGLE_SHEET_RANGE", "Sheet1!A1") # Если нужен диапазон

# --- Google Drive Folder Path --- (Удалено, так как URL передается через GUI)
# GOOGLE_DRIVE_FOLDER_URL = os.getenv("GOOGLE_DRIVE_FOLDER_URL")


# --- Data Files Paths ---
# Определяем базовую директорию проекта (где лежит .env или config.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Корень проекта
DATA_DIR = os.path.join(BASE_DIR, "data", "mappings")

CULTURES_FILE_PATH = os.path.join(DATA_DIR, "cultures.txt")
OPERATIONS_FILE_PATH = os.path.join(DATA_DIR, "operations.txt")
DEPARTMENTS_FILE_PATH = os.path.join(DATA_DIR, "departments.json")

# --- Report Output Path ---
REPORT_OUTPUT_PATH = os.getenv("REPORT_OUTPUT_PATH", os.path.join(BASE_DIR, "data", "reports", "processing_results.xlsx"))

# --- Quality Test Output ---
QUALITY_TEST_DIR = os.path.join(BASE_DIR, "data", "llm_quality_test") # Папка для результатов тестов

# --- Validation (Optional but recommended) ---
# Проверка наличия обязательных переменных
REQUIRED_ENV_VARS = {
    "deepseek": ["DEEPSEEK_API_KEY", "DEEPSEEK_API_BASE"], # Добавляем DEEPSEEK_API_BASE как обязательный для deepseek
    "openai": ["OPENAI_API_KEY"], # Добавляем проверку для openai
}

missing_vars = []
if PRIMARY_LLM_PROVIDER == "deepseek":
    for var in REQUIRED_ENV_VARS["deepseek"]:
        if not globals().get(var):
            missing_vars.append(var)
elif PRIMARY_LLM_PROVIDER == "openai": # Добавляем проверку для openai
    for var in REQUIRED_ENV_VARS["openai"]:
        if not globals().get(var):
            missing_vars.append(var)

if missing_vars:
    raise EnvironmentError(
        f"Ошибка: Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}. "
        f"Проверьте ваш .env файл."
    )




