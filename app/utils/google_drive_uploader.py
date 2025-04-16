import os
import logging
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
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

def upload_to_drive(file_path: str, filename: str = None) -> None:
    """
    Загружает файл на Google Drive в указанную папку.

    Args:
        file_path: Путь к локальному файлу.
        filename: Имя файла на Google Drive. Если не указано, берется имя исходного файла.
    """
    try:
        # Проверка пути к файлу
        if not os.path.exists(file_path):
            logging.error(f"Файл не найден: {file_path}")
            return

        # Авторизация через OAuth
        gauth = GoogleAuth()
        gauth.LoadClientConfigFile("app/client_secrets.json")
        gauth.LocalWebserverAuth()

        drive = GoogleDrive(gauth)

        # Получаем ID папки из ссылки
        folder_url = config.GOOGLE_DRIVE_FOLDER_URL
        if not folder_url or "drive.google.com" not in folder_url:
            logging.error("Некорректная или отсутствующая ссылка на Google Drive папку.")
            return
        folder_id = folder_url.split("/")[-1]

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
        logging.error(f"Ошибка при загрузке файла на Google Drive: {e}")
