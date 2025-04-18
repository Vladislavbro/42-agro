import os
import logging
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
# Импортируем oauth2client для обработки ошибки FileNotFoundError при загрузке кредов
# from oauth2client.client import FileNotFoundError # --- Удаляем этот импорт, FileNotFoundError - встроенное исключение
from app import config

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Маскируем чувствительное логирование от сторонних библиотек ---
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.getLogger('oauth2client').setLevel(logging.ERROR)
logging.getLogger('google.auth.transport.requests').setLevel(logging.WARNING)

class MaskOAuthURL(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if "accounts.google.com/o/oauth2/auth" in msg:
            record.msg = "[OAuth URL скрыт для безопасности]"
            record.args = ()
        return True

logger = logging.getLogger()
logger.addFilter(MaskOAuthURL())

# --- Пути к файлам --- 
# Определяем директорию текущего скрипта
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(UTILS_DIR, "drive_credentials.json")
# Путь к client_secrets.json остается прежним, так как он лежит в корне app
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(UTILS_DIR), "client_secrets.json")

def upload_to_drive(file_path: str, filename: str = None, google_drive_folder_url: str = None) -> None:
    """
    Загружает файл на Google Drive в указанную папку.

    Args:
        file_path: Путь к локальному файлу.
        filename: Имя файла на Google Drive. Если не указано, берется имя исходного файла.
        google_drive_folder_url: URL папки Google Drive. Если не указан, используется значение из config.
    """
    try:
        # Проверка пути к файлу
        if not os.path.exists(file_path):
            logging.error(f"Файл не найден: {file_path}")
            return

        # Авторизация через OAuth
        gauth = GoogleAuth()
        # Загружаем секреты клиента
        gauth.LoadClientConfigFile(CLIENT_SECRETS_FILE)

        # Пробуем загрузить сохраненные учетные данные из app/utils/drive_credentials.json
        try:
            gauth.LoadCredentialsFile(CREDENTIALS_FILE)
            if gauth.credentials is None:
                # Учетные данные не загрузились из файла: запускаем аутентификацию
                logging.info(f"Не удалось загрузить учетные данные из {CREDENTIALS_FILE}, запускаю веб-аутентификацию...")
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                # Учетные данные есть, но токен истек: обновляем
                logging.info("Токен доступа истек, обновляю...")
                gauth.Refresh()
            else:
                # Учетные данные валидны: авторизуемся
                gauth.Authorize()
                logging.info(f"Используются сохраненные учетные данные из {CREDENTIALS_FILE}.")
        except FileNotFoundError:
             # Файла нет: запускаем аутентификацию
             logging.info(f"Файл учетных данных {CREDENTIALS_FILE} не найден, запускаю веб-аутентификацию...")
             gauth.LocalWebserverAuth()
        except Exception as e:
            logging.error(f"Ошибка при загрузке/проверке учетных данных: {e}", exc_info=True)
            # Если с учетными данными проблема, прерываем выполнение, чтобы не падать дальше
            return

        # Сохраняем учетные данные (если были обновлены или получены впервые) в app/utils/drive_credentials.json
        try:
            gauth.SaveCredentialsFile(CREDENTIALS_FILE)
            logging.info(f"Учетные данные сохранены/обновлены в {CREDENTIALS_FILE}")
        except Exception as e:
            logging.error(f"Не удалось сохранить учетные данные в {CREDENTIALS_FILE}: {e}", exc_info=True)

        drive = GoogleDrive(gauth)

        # Получаем ID папки из ссылки
        # Приоритет у переданного URL, иначе берем из конфига
        folder_url = google_drive_folder_url or config.GOOGLE_DRIVE_FOLDER_URL

        if not folder_url or "drive.google.com" not in folder_url or "/folders/" not in folder_url:
            logging.error("Некорректная или отсутствующая ссылка на Google Drive папку.")
            return
        # Извлекаем ID папки из URL (должен быть последним элементом после /folders/)
        try:
            folder_id = folder_url.split('/folders/')[-1].split('?')[0] # Удаляем параметры типа ?usp=sharing
        except IndexError:
            logging.error(f"Не удалось извлечь ID папки из URL: {folder_url}")
            return

        # Создание и загрузка файла
        gfile = drive.CreateFile({
            'title': filename or os.path.basename(file_path),
            'parents': [{'id': folder_id}]
        })
        gfile.SetContentFile(file_path)
        gfile.Upload()

        file_id = gfile['id']
        file_link = f"https://drive.google.com/file/d/{file_id}/view"

        logging.info(f"Файл успешно загружен на Google Drive: {gfile['title']} (ID: {file_id})")
        logging.info(f"Ссылка на файл: {file_link}")

    except Exception as e:
        # Добавил exc_info для более детального лога ошибки
        logging.error(f"Общая ошибка при загрузке файла на Google Drive: {e}", exc_info=True)
