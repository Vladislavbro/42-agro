# Клиент для извлечения структурированных данных с помощью OpenAI Responses API
import datetime
import json
import logging
import traceback
from typing import List, Dict, Any, Optional
from openai import OpenAI # Прямой импорт OpenAI

# Импортируем переименованные константы
from .constants import OPENAI_REPORT_SCHEMA, OPENAI_SCHEMA_PROMPT

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenAISchemaExtractor:
    """
    Клиент для извлечения структурированных данных из текста
    с использованием OpenAI Responses API и JSON схемы.
    """
    def __init__(self, client: OpenAI):
        """
        Инициализирует клиент.

        Args:
            client: Инициализированный клиент OpenAI.
        """
        if not isinstance(client, OpenAI):
            raise TypeError("Параметр 'client' должен быть экземпляром openai.OpenAI")
        self.client = client
        # Схема будет браться из констант при вызове extract_data
        self.schema = OPENAI_REPORT_SCHEMA
        logger.info("Клиент OpenAISchemaExtractor инициализирован (используя Responses API).")

    def extract_data(self, 
                       input_message: str, 
                       cultures_list: str, 
                       operations_list: str, 
                       departments_list: str, 
                       model_name: str, 
                       prompt_template: str = OPENAI_SCHEMA_PROMPT
                       ) -> Optional[List[Dict[str, Any]]]:
        """
        Извлекает структурированные данные из агро-отчета, используя client.responses.create.

        Args:
            input_message: Строка с текстом сообщения.
            cultures_list: Строка со списком культур.
            operations_list: Строка со списком операций.
            departments_list: Строка со списком подразделений (JSON).
            model_name: Название модели OpenAI.
            prompt_template: Шаблон промпта. По умолчанию используется 
                             OPENAI_SCHEMA_PROMPT из constants.py.

        Returns:
            Список словарей с данными отчетов или None в случае ошибки.
        """
        current_date = datetime.date.today().isoformat()

        # Формируем промпт
        try:
            prompt = prompt_template.format(
                input_message=input_message,
                cultures_list=cultures_list,
                operations_list=operations_list,
                departments_list=departments_list,
                current_date=current_date
            )
        except KeyError as e:
            logger.error(f"Ошибка форматирования промпта: не найден ключ {e}")
            logger.debug("Убедитесь, что в шаблоне промпта нет лишних или неправильных фигурных скобок.")
            return None
        
        logger.info(f"Отправка запроса к OpenAI Responses API (модель: {model_name}).")
        # Вызываем API как в ноутбуке
        try:
            response = self.client.responses.create( # Используем responses.create
                model=model_name,
                input=[
                    {"role": "system", "content": "You are an AI assistant designed to extract structured data from agricultural reports according to a specific JSON schema."},
                    {"role": "user", "content": prompt} # Передаем отформатированный промпт
                ],
                text={ # Используем параметр text для передачи схемы
                    "format": {
                        "type": "json_schema",
                        "name": "report_schema", # Имя схемы
                        "strict": True,
                        "schema": self.schema # Используем схему из self.schema
                    }
                }
                # Убираем необязательные параметры для чистоты, можно добавить при необходимости
                # temperature=1,
                # max_output_tokens=3933,
                # top_p=0.6,
            )

            # Проверяем статус ответа
            if response.status == "incomplete":
                reason = response.incomplete_details.reason if response.incomplete_details else "unknown"
                logger.error(f"Ошибка: Ответ не завершен по причине: {reason}")
                return None
            elif response.status != "completed":
                error_details = response.error if response.error else "Нет деталей"
                logger.error(f"Ошибка: Неожиданный статус ответа: {response.status}. Детали: {error_details}")
                return None

            # Проверяем отказ
            if not response.output or not response.output[0].content:
                 logger.error("Ошибка: Неожиданная структура ответа, отсутствует output или content.")
                 logger.debug(f"Полный ответ: {response}")
                 return None

            output_content = response.output[0].content[0]

            if output_content.type == "refusal":
                refusal_message = output_content.refusal
                logger.error(f"Ошибка: Модель отказалась выполнять запрос: {refusal_message}")
                return None

            # Извлекаем текст
            if output_content.type != "output_text":
                 logger.error(f"Ошибка: Ответ не содержит ожидаемый тип 'output_text', получен тип '{output_content.type}'.")
                 logger.debug(f"Полный ответ: {response}")
                 return None

            raw_response_content = output_content.text
            logger.info("Получен и обработан ответ от OpenAI Responses API.")

            # Парсим JSON
            try:
                parsed_response_obj = json.loads(raw_response_content)
                if isinstance(parsed_response_obj, dict) and "reports" in parsed_response_obj:
                     parsed_data = parsed_response_obj.get('reports')
                     if not isinstance(parsed_data, list):
                          logger.error("Ошибка: Ключ 'reports' в ответе не содержит список.")
                          logger.debug(f"Ответ модели: {raw_response_content}")
                          return None
                else:
                     logger.error("Ошибка: Ответ модели не содержит ожидаемый ключ 'reports' или не является словарем.")
                     logger.debug(f"Ответ модели: {raw_response_content}")
                     return None

            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON ответа OpenAI: {e}")
                logger.debug(f"Ответ модели: {raw_response_content}")
                return None

            # Добавляем дату, если она null
            for item in parsed_data:
                if isinstance(item, dict) and item.get("Дата") is None:
                    item["Дата"] = current_date
            
            logger.info(f"Успешно извлечено {len(parsed_data)} записей.")
            return parsed_data

        except Exception as e:
            # Ловим все остальные ошибки (включая ошибки API)
            logger.error(f"Произошла общая ошибка при вызове OpenAI Responses API или обработке ответа: {e}")
            logger.debug(traceback.format_exc())
            return None 