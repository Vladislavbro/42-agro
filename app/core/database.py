# тестовый блок delete
import os, logging
logging.basicConfig(level=logging.INFO)
logging.info(f"📂 Current working directory: {os.getcwd()}")
#

from app.core.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import get_settings

# 2) Импортируем модуль с моделями — они сразу зарегистрируются в нашем Base
import app.models  # noqa: F401

# 3) Настройки и Engine
settings = get_settings()
engine = create_engine(
    settings.sqlite_url,
    connect_args={"check_same_thread": False},
)

# тестовый блок delete
import logging
logging.basicConfig(level=logging.INFO)
logging.info(f"=== SQLite URL in use: {settings.sqlite_url} ===")

# 4) Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 5) Создаём все таблицы, которых ещё нет
Base.metadata.create_all(bind=engine)

# delete
import logging
logging.info(f"🎯 Таблицы, зарегистрированные в Base.metadata: {list(Base.metadata.tables.keys())}")
