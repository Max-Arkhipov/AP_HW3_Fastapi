import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.main import app
from src.database import get_async_session
from src.base import Base
from src.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME
from jose import JWTError

# Настройка тестовой базы данных
TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
test_engine = create_async_engine(TEST_DATABASE_URL)
test_async_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Данные для тестов
TEST_USER = {"username": f"testuser_{asyncio.get_event_loop().time()}", "password": "testpassword"}
TEST_LINK_DATA = {
    "original_url": f"https://example.com/{asyncio.get_event_loop().time()}",
    "short_code": f"test{int(asyncio.get_event_loop().time())%10000}", # Example dynamic short code
    "expires_at": "2025-12-31T23:59:59.999Z", # Ensure future date for most tests
    "project": "pytest_project"
}

# Фикстура для создания и очистки таблиц
@pytest.fixture(scope="session", autouse=True)
async def init_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


# Фикстура для тестовой сессии
@pytest.fixture()
async def test_session():
    async with test_async_session_maker() as session:
        yield session
        await session.close()


# Переопределение зависимости для получения сессии
@pytest.fixture(autouse=True)
async def override_dependencies(test_session):
    async def get_test_session():
        yield test_session

    app.dependency_overrides[get_async_session] = get_test_session
    yield
    app.dependency_overrides.clear()


# Фикстура для event loop
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# Фикстура для регистрации пользователя и получения токена
import pytest
from httpx import AsyncClient


@pytest.fixture(scope="session")
async def auth_token():
    async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Попытка регистрации
        register_response = await client.post("/auth/register", json=TEST_USER)

        if register_response.status_code == 200:
            return register_response.json()["access_token"]

        # Если пользователь уже существует, логинимся
        login_response = await client.post(
            "/auth/login",
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
        )

        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        return login_response.json()["access_token"]


# Тест успешной регистрации
@pytest.mark.asyncio
async def test_register_success():
    client = TestClient(app)
    response = client.post("/auth/register", json=TEST_USER)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


# Тесты для роутеров ссылок
@pytest.mark.asyncio
async def test_shorten_link(auth_token):
    client = TestClient(app)
    response = client.post(
        "links/shorten",
        json=TEST_LINK_DATA,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert "short_code" in response.json()


@pytest.mark.asyncio
async def test_get_link():
    client = TestClient(app)
    response = client.get(f"links/get_link/{TEST_LINK_DATA['short_code']}")
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_update_link(auth_token):
    client = TestClient(app)
    token = await auth_token
    response = client.put(
        f"/links/put_link/{TEST_LINK_DATA['short_code']}",
        json={"new_url": "https://updated.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_link_stats():
    client = TestClient(app)
    response = client.get(f"/stats/{TEST_LINK_DATA['short_code']}")
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_search_link(auth_token):
    client = TestClient(app)
    response = client.get(
        "/search", params={"original_url": "https://updated.com"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_expired_links(auth_token):
    client = TestClient(app)
    token = await auth_token
    response = client.get(
        "/links/expired",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_links_by_project(auth_token):
    client = TestClient(app)
    token = await auth_token
    response = client.get(
        f"/links/project/{TEST_LINK_DATA['project']}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_link(auth_token):
    client = TestClient(app)
    token = await auth_token
    response = client.delete(
        f"/delete_link/{TEST_LINK_DATA['short_code']}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 404]
