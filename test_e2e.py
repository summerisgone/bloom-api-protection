import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx import ASGITransport
from main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def bad_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.cookies.set("session_id", "invalid_session")
        yield client

@pytest.mark.asyncio
async def test_api_protection(client: AsyncClient, bad_client: AsyncClient):
    # Тест 1: Прямой запрос к API без посещения главной страницы
    response = await client.post("/api/suggestions", json={"query": "test"})
    assert response.status_code == 400
    assert "Это API доступно только через веб-интерфейс" in response.text

    # Тест 2: Запрос к API после посещения главной страницы
    # Сначала посещаем главную страницу
    response = await client.get("/")
    assert response.status_code == 200
    session_id = client.cookies.get("session_id")
    assert session_id is not None

    # Теперь делаем запрос к API
    response = await client.post("/api/suggestions", json={"query": "test"})
    assert response.status_code == 200

    # Тест 3: Запрос к API с неверной сессией
    response = await bad_client.post("/api/suggestions", json={"query": "test"})
    assert response.status_code == 400
    assert "Это API доступно только через веб-интерфейс" in response.text

    # Тест 4: Проверка сохранения URL в фильтре
    # Делаем несколько запросов к разным URL
    await client.get("/static/css/styles.css")
    await client.get("/static/js/main.js")
    
    # Проверяем, что API все еще доступно
    response = await client.post("/api/suggestions", json={"query": "test"})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_session_persistence(client: AsyncClient):
    # Тест 1: Проверка сохранения сессии между запросами
    response = await client.get("/")
    session_id = response.cookies.get("session_id")
    assert session_id is not None
    
    # Делаем несколько запросов к API
    for _ in range(3):
        response = await client.post("/api/suggestions", json={"query": "test"})
        assert response.status_code == 200
        # Проверяем, что в клиенте сохранена та же сессия
        assert client.cookies.get("session_id") == session_id

@pytest.mark.asyncio
async def test_multiple_sessions(client: AsyncClient):
    # Тест 1: Проверка работы с разными сессиями
    # Создаем второй клиент
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client2:
        # Первый клиент посещает главную страницу
        response1 = await client.get("/")
        session_id1 = response1.cookies.get("session_id")
        
        # Второй клиент посещает главную страницу
        response2 = await client2.get("/")
        session_id2 = response2.cookies.get("session_id")
        
        # Проверяем, что сессии разные
        assert session_id1 != session_id2
        
        # Проверяем, что оба клиента могут использовать API
        response1 = await client.post("/api/suggestions", json={"query": "test"})
        response2 = await client2.post("/api/suggestions", json={"query": "test"})
        
        assert response1.status_code == 200
        assert response2.status_code == 200 