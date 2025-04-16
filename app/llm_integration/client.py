# Код для инициализации клиента LLM (DeepSeek/OpenAI) и отправки запросов 
import os
import logging
import datetime # Добавил datetime для примера
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
        self.client = None
        self.model_name = None # Модель будет определена при инициализации

        logging.info(f"Инициализация LLM клиента для провайдера: {self.provider}")

        if self.provider == "deepseek":
            if not config.DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY не найден в конфигурации.")
            try:
                # Укажем base_url, если он есть в конфиге
                base_url = getattr(config, 'DEEPSEEK_API_BASE', None) # Используем getattr для опциональной переменной
                if base_url:
                     self.client = OpenAI(
                        api_key=config.DEEPSEEK_API_KEY,
                        base_url=base_url
                    )
                     logging.info(f"Используется DeepSeek API с базовым URL: {base_url}")
                else:
                     self.client = OpenAI(
                        api_key=config.DEEPSEEK_API_KEY,
                        base_url="https://api.deepseek.com/v1" # Стандартный URL DeepSeek
                    )
                     logging.info("Используется стандартный DeepSeek API URL.")

                # Используем имя модели из конфига
                self.model_name = config.DEEPSEEK_MODEL_NAME
                # Проверка доступности модели (опционально, может вызвать ошибку если API недоступен)
                # self.client.models.retrieve(self.model_name)
                logging.info(f"Клиент DeepSeek (OpenAI SDK) успешно инициализирован для модели: {self.model_name}")
            except Exception as e:
                logging.error(f"Ошибка инициализации клиента DeepSeek: {e}")
                raise ConnectionError(f"Не удалось инициализировать клиент DeepSeek: {e}")

        elif self.provider == "openai": # Обработка OpenAI
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY не найден в конфигурации.")
            try:
                self.client = OpenAI(api_key=config.OPENAI_API_KEY)
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

    

