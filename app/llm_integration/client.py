# Код для инициализации клиента LLM (DeepSeek/OpenAI) и отправки запросов 
import os
import logging
import datetime # Добавил datetime для примера
import asyncio # Добавлено
import aiohttp # Добавлено
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError

try:
    from app import config
except ImportError:
    # Если запуск происходит не из корня проекта, пробуем относительный импорт
    import config

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TextGenerationClient:
    """
    Клиент для взаимодействия с OpenAI-совместимым LLM API (DeepSeek или OpenAI)
    для генерации текста.

    Инициализирует клиент для одного из провайдеров на основе конфигурации
    и предоставляет унифицированный метод для генерации ответа.
    """
    def __init__(self):
        """Инициализирует клиент LLM на основе настроек в config."""
        self.provider = config.PRIMARY_LLM_PROVIDER
        self.client = None # Синхронный клиент
        self.model_name = None
        self.api_key = None # Добавлено
        self.base_url = None # Добавлено

        logging.info(f"Инициализация LLM клиента для провайдера: {self.provider}")

        if self.provider == "deepseek":
            self.api_key = config.DEEPSEEK_API_KEY # Сохраняем ключ
            if not self.api_key:
                raise ValueError("DEEPSEEK_API_KEY не найден в конфигурации.")
            try:
                # Укажем base_url, если он есть в конфиге
                self.base_url = getattr(config, 'DEEPSEEK_API_BASE', "https://api.deepseek.com/v1") # Сохраняем URL
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                logging.info(f"Используется DeepSeek API с базовым URL: {self.base_url}")
                # Используем имя модели из конфига
                self.model_name = config.DEEPSEEK_MODEL_NAME
                # Проверка доступности модели (опционально, может вызвать ошибку если API недоступен)
                # self.client.models.retrieve(self.model_name)
                logging.info(f"Клиент DeepSeek (OpenAI SDK) успешно инициализирован для модели: {self.model_name}")
            except Exception as e:
                logging.error(f"Ошибка инициализации клиента DeepSeek: {e}")
                raise ConnectionError(f"Не удалось инициализировать клиент DeepSeek: {e}")

        elif self.provider == "openai": # Обработка OpenAI
            self.api_key = config.OPENAI_API_KEY # Сохраняем ключ
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY не найден в конфигурации.")
            try:
                # Для OpenAI стандартный base_url обычно не указывается явно при использовании библиотеки,
                # но для единообразия и прямого HTTP-запроса его можно определить.
                # Библиотека openai сама формирует URL, но для aiohttp он нам нужен.
                # Предположим стандартный URL OpenAI API v1.
                self.base_url = "https://api.openai.com/v1" # Сохраняем стандартный URL
                self.client = OpenAI(api_key=self.api_key) # Оставляем синхронный клиент
                self.model_name = config.OPENAI_MODEL_NAME
                logging.info(f"Клиент OpenAI успешно инициализирован для модели: {self.model_name}")
            except Exception as e:
                logging.error(f"Ошибка инициализации клиента OpenAI: {e}")
                raise ConnectionError(f"Не удалось инициализировать клиент OpenAI: {e}")

        else:
            # Обновляем сообщение об ошибке, так как Gemini больше не поддерживается
            raise ValueError(f"Неподдерживаемый или неверный LLM провайдер указан в конфигурации: {self.provider}. Поддерживаются 'openai' и 'deepseek'.")

    def generate_response(self, prompt: str, temperature: float = 0.2) -> str | None:
        """
        Отправляет промпт к инициализированному LLM API и возвращает ответ.

        Args:
            prompt: Текст промпта для LLM.
            temperature: Температура генерации (для воспроизводимости лучше низкая).

        Returns:
            Текстовый ответ от LLM или None в случае ошибки.
        """
        if not self.client:
            logging.error("LLM клиент не инициализирован.")
            return None

        logging.info(f"Отправка запроса к {self.provider} (модель: {self.model_name}).")

        if self.provider in ["deepseek", "openai"]:
            return self._generate_openai_compatible_response(prompt, temperature)
        else:
            # Эта ветка теоретически не должна достигаться из-за проверки в __init__
            logging.error(f"Неизвестный провайдер {self.provider} в generate_response.")
            return None
    
    def _generate_openai_compatible_response(self, prompt: str, temperature: float) -> str | None:
        """Генерирует ответ с использованием OpenAI-совместимого API (OpenAI, DeepSeek)."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an AI assistant designed to extract structured data from agricultural reports according to specific instructions and format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                # max_tokens=... # Можно добавить ограничение
                # timeout=... # Можно добавить таймаут
            )
            # logging.debug(f"Полный ответ {self.provider}: {response}")
            if response.choices:
                content = response.choices[0].message.content
                logging.info(f"Получен ответ от {self.provider}.")
                # logging.debug(f"Текст ответа: {content[:200]}...")
                return content.strip()
            else:
                logging.warning(f"{self.provider} вернул ответ без 'choices'.")
                return None
        # Обработка специфичных ошибок OpenAI (применимо и к DeepSeek через SDK)
        except APITimeoutError:
            logging.error(f"Ошибка: Запрос к {self.provider} API превысил таймаут.")
            return None
        except APIConnectionError as e:
            logging.error(f"Ошибка: Не удалось подключиться к {self.provider} API: {e}")
            return None
        except RateLimitError:
            logging.error(f"Ошибка: Превышен лимит запросов к {self.provider} API.")
            return None
        except APIStatusError as e:
             logging.error(f"Ошибка: {self.provider} API вернул статус ошибки {e.status_code}: {e.response}")
             return None
        except Exception as e:
            logging.error(f"Непредвиденная ошибка при запросе к {self.provider} API: {e}")
            return None

    async def generate_response_async(self, session: aiohttp.ClientSession, prompt: str, temperature: float = 0.2) -> str | None:
        """
        Асинхронно отправляет промпт к инициализированному LLM API через aiohttp и возвращает ответ.

        Args:
            session: Экземпляр aiohttp.ClientSession.
            prompt: Текст промпта для LLM.
            temperature: Температура генерации.

        Returns:
            Текстовый ответ от LLM или None в случае ошибки.
        """
        if not self.api_key or not self.base_url:
            logging.error("LLM клиент не полностью инициализирован для асинхронного запроса (api_key или base_url отсутствует).")
            return None

        logging.info(f"Асинхронная отправка запроса к {self.provider} (модель: {self.model_name}).")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are an AI assistant designed to extract structured data from agricultural reports according to specific instructions and format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            # "max_tokens": ... # Можно добавить ограничение
        }
        # Формируем полный URL для эндпоинта чата
        chat_url = f"{self.base_url.rstrip('/')}/chat/completions"

        try:
            # Устанавливаем таймаут для запроса
            timeout = aiohttp.ClientTimeout(total=60) # 60 секунд общий таймаут
            async with session.post(chat_url, headers=headers, json=payload, timeout=timeout) as response:
                # response.raise_for_status() # Проверяет статус ответа (4xx, 5xx) и вызывает исключение
                if response.status == 200:
                    data = await response.json()
                    # logging.debug(f"Полный асинхронный ответ {self.provider}: {data}")
                    if data.get("choices"):
                        content = data["choices"][0].get("message", {}).get("content")
                        if content:
                             logging.info(f"Получен асинхронный ответ от {self.provider}.")
                             return content.strip()
                        else:
                             logging.warning(f"{self.provider} вернул ответ без 'content' в 'message'.")
                             return None
                    else:
                        logging.warning(f"{self.provider} вернул ответ без 'choices'. Ответ: {data}")
                        return None
                else:
                    error_text = await response.text()
                    logging.error(f"Ошибка от {self.provider} API. Статус: {response.status}, Ответ: {error_text}")
                    return None
        except asyncio.TimeoutError:
            logging.error(f"Ошибка: Запрос к {self.provider} API ({chat_url}) превысил таймаут.")
            return None
        except aiohttp.ClientConnectorError as e:
            logging.error(f"Ошибка соединения при запросе к {self.provider} API ({chat_url}): {e}")
            return None
        except aiohttp.ClientResponseError as e: # Обработка ошибок, возбуждаемых raise_for_status()
            logging.error(f"Ошибка ответа от {self.provider} API ({chat_url}). Статус: {e.status}, Сообщение: {e.message}")
            return None
        except Exception as e:
            logging.error(f"Непредвиденная ошибка при асинхронном запросе к {self.provider} API ({chat_url}): {e}")
            return None

    

