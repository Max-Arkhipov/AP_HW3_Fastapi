import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.main import app
from src.database import get_async_session
from src.base import Base
from src.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

# Настройка тестовой базы данных
TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
test_engine = create_async_engine(TEST_DATABASE_URL)
test_async_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhcmtoaXBvdm0iLCJleHAiOjE3NDM0NDQzNDd9.WGwWXqn_MstN2m2hSyI0ybeIFMOa6bZxTIr1DsZkjqs"

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


# Тест успешной регистрации
@pytest.mark.asyncio
async def test_register_success():
    client = TestClient(app)
    response = client.post(
        "/auth/register",
        json={"username": "testuser37", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


# Тесты для роутеров ссылок
@pytest.mark.asyncio
async def test_shorten_link():
    client = TestClient(app)
    response = client.post("links/shorten", json={"original_url": "https://example.com",
                                             "short_code": "abc126",
                                             "expires_at": "2025-04-30T14:10:16.009Z",
                                             "project": "test_project"})
    assert response.status_code == 200
    assert "short_code" in response.json()


@pytest.mark.asyncio
async def test_get_link():
    client = TestClient(app)
    short_code = "abc126"
    response = client.get(f"links/get_link/{short_code}")
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_update_link():
    client = TestClient(app)

    token = auth_token

    short_code = "abc3456"
    response = client.put(
        f"/links/put_link/{short_code}",
        json={"new_url": "https://updated.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_get_link_stats():
    client = TestClient(app)
    short_code = "abc3456"
    response = client.get(f"/stats/{short_code}")
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_search_link():
    client = TestClient(app)

    token = auth_token

    response = client.get("/search", params={"original_url": "https://updated.com"},
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_expired_links():
    client = TestClient(app)

    token = auth_token

    response = client.get("/links/expired",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_links_by_project():
    client = TestClient(app)

    token = auth_token

    response = client.get("/links/project/test_project",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_link():
    client = TestClient(app)

    token = auth_token

    short_code = "abc3456"
    response = client.delete(f"/delete_link/{short_code}",
                             headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in [200, 404]