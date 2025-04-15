import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
# Ищем .env файл начиная с директории, где находится config.py, и поднимаясь выше
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') # Путь к .env в корне проекта
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    # Если .env не найден в корне, попробуем загрузить из текущей директории 
    # (на случай запуска скриптов не из корня)
    load_dotenv() 

# --- LLM Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# Можно добавить DEEPSEEK_API_BASE, если планируете использовать
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE") # Добавляем загрузку base_url для DeepSeek
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Добавляем загрузку ключа OpenAI
PRIMARY_LLM_PROVIDER = os.getenv("PRIMARY_LLM_PROVIDER", "deepseek").lower() # По умолчанию deepseek

# --- Model Names --- (Заданы константами)
DEEPSEEK_MODEL_NAME = "deepseek-chat"
GEMINI_MODEL_NAME = "gemini-2.0-flash" # Используем указанную модель
OPENAI_MODEL_NAME = "gpt-4.1-mini" # Используем указанную модель

# --- Google Sheets Configuration ---
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# GOOGLE_SHEET_RANGE = os.getenv("GOOGLE_SHEET_RANGE", "Sheet1!A1") # Если нужен диапазон

# --- Data Files Paths ---
# Определяем базовую директорию проекта (где лежит .env или config.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Корень проекта
DATA_DIR = os.path.join(BASE_DIR, "data", "mappings")

CULTURES_FILE_PATH = os.path.join(DATA_DIR, "cultures.txt")
OPERATIONS_FILE_PATH = os.path.join(DATA_DIR, "operations.txt")
DEPARTMENTS_FILE_PATH = os.path.join(DATA_DIR, "departments.json")

# --- Validation (Optional but recommended) ---
# Проверка наличия обязательных переменных
REQUIRED_ENV_VARS = {
    "deepseek": ["DEEPSEEK_API_KEY", "DEEPSEEK_API_BASE"], # Добавляем DEEPSEEK_API_BASE как обязательный для deepseek
    "gemini": ["GEMINI_API_KEY"],
    "openai": ["OPENAI_API_KEY"], # Добавляем проверку для openai
    "google": ["GOOGLE_SHEET_ID", "GOOGLE_APPLICATION_CREDENTIALS"]
}

missing_vars = []
if PRIMARY_LLM_PROVIDER == "deepseek":
    for var in REQUIRED_ENV_VARS["deepseek"]:
        if not globals().get(var):
            missing_vars.append(var)
elif PRIMARY_LLM_PROVIDER == "gemini":
     for var in REQUIRED_ENV_VARS["gemini"]:
        if not globals().get(var):
            missing_vars.append(var)
elif PRIMARY_LLM_PROVIDER == "openai": # Добавляем проверку для openai
    for var in REQUIRED_ENV_VARS["openai"]:
        if not globals().get(var):
            missing_vars.append(var)

for var in REQUIRED_ENV_VARS["google"]:
     if not globals().get(var):
         missing_vars.append(var)

if missing_vars:
    raise EnvironmentError(
        f"Ошибка: Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}. "
        f"Проверьте ваш .env файл."
    )

if GOOGLE_APPLICATION_CREDENTIALS and not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
     print(
         f"Внимание: Файл учетных данных Google '{GOOGLE_APPLICATION_CREDENTIALS}' не найден. "
         f"Убедитесь, что путь в .env указан верно."
     )
     # Можно либо выбросить исключение, либо просто предупредить
     # raise FileNotFoundError(f"Файл учетных данных Google не найден: {GOOGLE_APPLICATION_CREDENTIALS}")
