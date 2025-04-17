from functools import lru_cache
from pathlib import Path
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # Новый стиль конфигурации Pydantic v2:
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"          # игнорировать все прочие ENV‑переменные
    )

    deepseek_url: str = Field("http://localhost:9000", env="DEEPSEEK_URL")
    demo_mode:   bool = Field(True,                   env="DEMO_MODE")
    # формируем правильный Windows URI: три слэша + абсолютный путь с прямыми слешами
    sqlite_url:  str = Field(
        f"sqlite:///{(BASE_DIR / 'reports.db').as_posix()}",
        env="SQLITE_URL"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()

# delete
print(f"🔥 BASE_DIR resolved to: {BASE_DIR}")