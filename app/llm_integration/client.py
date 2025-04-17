# Код для инициализации клиента LLM (DeepSeek/OpenAI) и отправки запросов 
import os
import logging
import datetime # Добавил datetime для примера
import asyncio # Добавлено
import aiohttp # Добавлено
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError, AsyncOpenAI
from abc import ABC, abstractmethod

try:
    from app import config
    from app.llm_integration.constants import SYSTEM_ROLE_CONTENT # Импортируем константу
except ImportError:
    # Если запуск происходит не из корня проекта, пробуем относительный импорт
    import config
    # Попытка импорта константы при запуске не из корня (может не сработать без __init__.py)
    try:
        from llm_integration.constants import SYSTEM_ROLE_CONTENT
    except ImportError:
         # Запасной вариант, если импорт не сработал
        SYSTEM_ROLE_CONTENT = (
            "You are an AI assistant designed to extract structured data "
            "from agricultural reports according to specific instructions and format."
        )
        logging.warning("Не удалось импортировать SYSTEM_ROLE_CONTENT из constants.py, используется значение по умолчанию.")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BaseLLMClient(ABC):
    """Абстрактный базовый класс для клиентов LLM."""
    def __init__(self):
        self.provider = "unknown"
        self.model_name = "unknown"
        self.temperature = config.LLM_TEMPERATURE # Сохраняем температуру из конфига
        logging.info(f"Инициализация LLM клиента для провайдера: {self.provider}")

    @abstractmethod
    def generate_response(self, prompt: str, temperature: float | None = None) -> str | None:
        """Синхронно генерирует ответ от LLM."""
        pass

    @abstractmethod
    async def generate_response_async(self, session: aiohttp.ClientSession, prompt: str, temperature: float | None = None) -> str | None:
        """Асинхронно генерирует ответ от LLM."""
        pass


class DeepSeekClient(BaseLLMClient):
    def __init__(self):
        super().__init__() # Вызываем __init__ базового класса
        self.provider = "deepseek"
        self.model_name = config.DEEPSEEK_MODEL_NAME
        self.client = None
        self.async_client = None
        try:
            # Используем synchronous OpenAI client для DeepSeek совместимого API
            self.client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_API_BASE)
            # Используем asynchronous OpenAI client
            self.async_client = AsyncOpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_API_BASE)
            logging.info(f"Клиент DeepSeek ({self.provider}) успешно инициализирован для модели: {self.model_name}")
        except Exception as e:
            logging.error(f"Ошибка инициализации клиента DeepSeek: {e}")
            raise

    def generate_response(self, prompt: str, temperature: float | None = None) -> str | None:
        if not self.client:
            logging.error("Клиент DeepSeek не инициализирован.")
            return None
        
        temp_to_use = temperature if temperature is not None else self.temperature
        logging.info(f"Отправка запроса к DeepSeek (модель: {self.model_name}, температура: {temp_to_use})...")

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_ROLE_CONTENT},
                    {"role": "user", "content": prompt}
                ],
                model=self.model_name,
                temperature=temp_to_use,
            )
            response_content = chat_completion.choices[0].message.content
            logging.info("Ответ от DeepSeek получен.")
            return response_content
        except Exception as e:
            logging.error(f"Ошибка при вызове API DeepSeek: {e}")
            return None

    async def generate_response_async(self, session: aiohttp.ClientSession, prompt: str, temperature: float | None = None) -> str | None:
        # AsyncOpenAI клиент использует свою внутреннюю сессию, поэтому session из aiohttp не нужен
        if not self.async_client:
            logging.error("Асинхронный клиент DeepSeek не инициализирован.")
            return None

        temp_to_use = temperature if temperature is not None else self.temperature
        logging.info(f"Отправка асинхронного запроса к DeepSeek (модель: {self.model_name}, температура: {temp_to_use})...")

        try:
            chat_completion = await self.async_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_ROLE_CONTENT},
                    {"role": "user", "content": prompt}
                ],
                model=self.model_name,
                temperature=temp_to_use,
            )
            response_content = chat_completion.choices[0].message.content
            logging.info("Асинхронный ответ от DeepSeek получен.")
            return response_content
        except Exception as e:
            logging.error(f"Ошибка при асинхронном вызове API DeepSeek: {e}")
            return None


class OpenAIClient(BaseLLMClient):
    def __init__(self):
        super().__init__() # Вызываем __init__ базового класса
        self.provider = "openai"
        self.model_name = config.OPENAI_MODEL_NAME
        self.client = None
        self.async_client = None
        try:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.async_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            logging.info(f"Клиент OpenAI ({self.provider}) успешно инициализирован для модели: {self.model_name}")
        except Exception as e:
            logging.error(f"Ошибка инициализации клиента OpenAI: {e}")
            raise

    def generate_response(self, prompt: str, temperature: float | None = None) -> str | None:
        if not self.client:
            logging.error("Клиент OpenAI не инициализирован.")
            return None
        
        temp_to_use = temperature if temperature is not None else self.temperature
        logging.info(f"Отправка запроса к OpenAI (модель: {self.model_name}, температура: {temp_to_use})...")

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_ROLE_CONTENT},
                    {"role": "user", "content": prompt}
                ],
                model=self.model_name,
                temperature=temp_to_use,
            )
            response_content = chat_completion.choices[0].message.content
            logging.info("Ответ от OpenAI получен.")
            return response_content
        except Exception as e:
            logging.error(f"Ошибка при вызове API OpenAI: {e}")
            return None

    async def generate_response_async(self, session: aiohttp.ClientSession, prompt: str, temperature: float | None = None) -> str | None:
        if not self.async_client:
            logging.error("Асинхронный клиент OpenAI не инициализирован.")
            return None
        
        temp_to_use = temperature if temperature is not None else self.temperature
        logging.info(f"Отправка асинхронного запроса к OpenAI (модель: {self.model_name}, температура: {temp_to_use})...")

        try:
            chat_completion = await self.async_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_ROLE_CONTENT},
                    {"role": "user", "content": prompt}
                ],
                model=self.model_name,
                temperature=temp_to_use,
            )
            response_content = chat_completion.choices[0].message.content
            logging.info("Асинхронный ответ от OpenAI получен.")
            return response_content
        except Exception as e:
            logging.error(f"Ошибка при асинхронном вызове API OpenAI: {e}")
            return None

# Фабричная функция для создания клиента
def TextGenerationClient() -> BaseLLMClient:
    provider = config.PRIMARY_LLM_PROVIDER
    if provider == "deepseek":
        return DeepSeekClient()
    elif provider == "openai":
        return OpenAIClient()
    else:
        raise ValueError(f"Неизвестный провайдер LLM: {provider}")

    

