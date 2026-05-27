"""
Модуль настройки асинхронного подключения к базе данных PostgreSQL.

Использует SQLAlchemy 2.0+ с поддержкой async/await.
Настраивает движок (engine), фабрику сессий и базовый класс для моделей.
Загружает параметры подключения из переменных окружения (.env).

Пример .env:
    DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

Требует установленного пакета: asyncpg
"""
# --------------- Асинхронное подключение к PostgreSQL -------------------------
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Создаём Engine
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Настраиваем фабрику сеансов
async_sessionmaker = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

# Определяем базовый класс для моделей
class Base(DeclarativeBase):
    pass