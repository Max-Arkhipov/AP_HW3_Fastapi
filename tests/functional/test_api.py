import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.main import app  # Предполагается, что ваше приложение определено в src.main
from src.database import get_async_session
from src.base import Base
from src.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

# Настройка тестовой базы данных в памяти
TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"  # Замените на ваши данные
test_engine = create_async_engine(TEST_DATABASE_URL)
test_async_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

# Фикстура для создания и очистки таблиц
@pytest.fixture(autouse=True)
async def init_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Создаем таблицы
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Удаляем таблицы

# Фикстура для переопределения зависимости на тестовую сессию
@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_async_session] = lambda: test_async_session_maker()
    yield
    app.dependency_overrides.clear()

# Тест успешной регистрации
@pytest.mark.asyncio
async def test_register_success():
    client = TestClient(app)
    response = client.post(
        "/auth/register",
        json={"username": "testuser5", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

# Тест регистрации с уже существующим пользователем
@pytest.mark.asyncio
async def test_register_existing_user():
    client = TestClient(app)
    # Сначала регистрируем пользователя
    client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )
    # Пытаемся зарегистрировать того же пользователя еще раз
    response = client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 400  # Ожидаем ошибку, так как username уникален

# Тест успешной авторизации
@pytest.mark.asyncio
async def test_login_success():
    client = TestClient(app)
    # Сначала регистрируем пользователя
    client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )
    # Пытаемся авторизоваться
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

# Тест авторизации с неправильным паролем
@pytest.mark.asyncio
async def test_login_invalid_password():
    client = TestClient(app)
    # Сначала регистрируем пользователя
    client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )
    # Пытаемся авторизоваться с неправильным паролем
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401  # Ожидаем ошибку аутентификации