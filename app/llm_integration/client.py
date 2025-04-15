# Код для инициализации клиента LLM (DeepSeek/Gemini) и отправки запросов 
import os
import logging
import datetime # Добавил datetime для примера
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError
import google.generativeai as genai
# Импортируем конфигурацию из app.config
# Предполагается, что app/ находится в PYTHONPATH или используется относительный импорт
try:
    from app import config
except ImportError:
    # Если запуск происходит не из корня проекта, пробуем относительный импорт
    import config

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TextGenerationClient:
    """
    Клиент для взаимодействия с LLM API (DeepSeek или Gemini) для генерации текста.

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
                # DeepSeek использует OpenAI SDK
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

        elif self.provider == "gemini":
            if not config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY не найден в конфигурации.")
            try:
                genai.configure(api_key=config.GEMINI_API_KEY)
                # Используем имя модели из конфига
                self.model_name = config.GEMINI_MODEL_NAME
                self.client = genai.GenerativeModel(self.model_name)
                 # Проверка доступности (простой запрос)
                # Оборачиваем в try-except, т.к. generate_content может выбросить исключение при проблемах
                try:
                    self.client.generate_content("test", generation_config=genai.types.GenerationConfig(candidate_count=1, max_output_tokens=5))
                except Exception as gen_e:
                    logging.warning(f"Не удалось выполнить тестовый запрос к Gemini: {gen_e}")
                    # Не прерываем инициализацию, но предупреждаем
                logging.info(f"Клиент Gemini успешно инициализирован для модели: {self.model_name}")
            except Exception as e:
                logging.error(f"Ошибка инициализации клиента Gemini: {e}")
                raise ConnectionError(f"Не удалось инициализировать клиент Gemini: {e}")

        elif self.provider == "openai": # Добавляем обработку OpenAI
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY не найден в конфигурации.")
            try:
                self.client = OpenAI(api_key=config.OPENAI_API_KEY)
                # Используем имя модели из конфига
                self.model_name = config.OPENAI_MODEL_NAME
                # Проверка доступности модели (опционально)
                # self.client.models.retrieve(self.model_name)
                logging.info(f"Клиент OpenAI успешно инициализирован для модели: {self.model_name}")
            except Exception as e:
                logging.error(f"Ошибка инициализации клиента OpenAI: {e}")
                raise ConnectionError(f"Не удалось инициализировать клиент OpenAI: {e}")

        else:
            raise ValueError(f"Неподдерживаемый LLM провайдер указан в конфигурации: {self.provider}")

    def _generate_deepseek_response(self, prompt: str, temperature: float) -> str | None:
        """Генерирует ответ с использованием DeepSeek API."""
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
            # logging.debug(f"Полный ответ DeepSeek: {response}")
            if response.choices:
                content = response.choices[0].message.content
                logging.info(f"Получен ответ от {self.provider}.")
                # logging.debug(f"Текст ответа: {content[:200]}...")
                return content.strip()
            else:
                logging.warning(f"{self.provider} вернул ответ без 'choices'.")
                return None
        # Обработка специфичных ошибок OpenAI/DeepSeek
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

    def _generate_gemini_response(self, prompt: str, temperature: float) -> str | None:
        """Генерирует ответ с использованием Gemini API."""
        response = None # Инициализируем response
        try:
            response = self.client.generate_content(
                contents=prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    temperature=temperature
                    # max_output_tokens=... # Можно добавить ограничение
                )
            )
            # logging.debug(f"Полный ответ Gemini: {response}")
            # Проверка на наличие блокировки контента
            if not response.candidates:
                 logging.warning(f"Gemini API не вернул кандидатов. Возможно, контент заблокирован.")
                 if hasattr(response, 'prompt_feedback'):
                     logging.warning(f"Gemini Prompt Feedback: {response.prompt_feedback}")
                 return None

            # Обработка возможной ошибки в частях ответа
            if response.candidates[0].content.parts:
                content = response.candidates[0].content.parts[0].text
                logging.info(f"Получен ответ от {self.provider}.")
                # logging.debug(f"Текст ответа: {content[:200]}...")
                return content.strip()
            else:
                logging.warning(f"Gemini API вернул кандидата без 'parts'.")
                if hasattr(response, 'prompt_feedback'):
                     logging.warning(f"Gemini Prompt Feedback: {response.prompt_feedback}")
                return None
        # Обработка общих ошибок Gemini и других
        except Exception as e:
            logging.error(f"Непредвиденная ошибка при запросе к {self.provider} API: {e}")
            # Дополнительно логируем фидбек Gemini, если он есть
            if response and hasattr(response, 'prompt_feedback'):
                 logging.warning(f"Gemini Prompt Feedback: {response.prompt_feedback}")
            return None

    # Добавляем метод для OpenAI (очень похож на DeepSeek, но без base_url и другая модель)
    def _generate_openai_response(self, prompt: str, temperature: float) -> str | None:
        """Генерирует ответ с использованием OpenAI API."""
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
            # logging.debug(f"Полный ответ OpenAI: {response}")
            if response.choices:
                content = response.choices[0].message.content
                logging.info(f"Получен ответ от {self.provider}.")
                # logging.debug(f"Текст ответа: {content[:200]}...")
                return content.strip()
            else:
                logging.warning(f"{self.provider} вернул ответ без 'choices'.")
                return None
        # Обработка специфичных ошибок OpenAI
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

        if self.provider == "deepseek":
            return self._generate_deepseek_response(prompt, temperature)
        elif self.provider == "gemini":
            return self._generate_gemini_response(prompt, temperature)
        elif self.provider == "openai": # Добавляем вызов для OpenAI
            return self._generate_openai_response(prompt, temperature)
        else:
            # Эта ветка не должна достигаться из-за проверки в __init__, но на всякий случай
            logging.error(f"Неизвестный провайдер {self.provider} в generate_response.")
            return None

