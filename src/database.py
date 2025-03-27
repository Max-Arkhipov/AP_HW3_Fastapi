from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

# Формирование строки подключения
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создание асинхронного движка
engine = create_async_engine(DATABASE_URL)

# Базовый класс для моделей
Base = declarative_base()

# Фабрика асинхронных сессий
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Генератор для получения сессии
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# Функция для инициализации базы данных (создание таблиц)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)