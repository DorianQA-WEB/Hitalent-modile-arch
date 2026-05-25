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