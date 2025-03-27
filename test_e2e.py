import pytest
from fastapi.testclient import TestClient
from main import app
import httpx
from typing import Generator

client = TestClient(app)

def test_api_protection():
    # Тест 1: Прямой запрос к API без посещения главной страницы
    response = client.post("/api/suggestions", json={"query": "test"})
    assert response.status_code == 400
    assert "Это API доступно только через веб-интерфейс" in response.text

    # Тест 2: Запрос к API после посещения главной страницы
    # Сначала посещаем главную страницу
    response = client.get("/")
    assert response.status_code == 200
    session_id = response.cookies.get("session_id")
    assert session_id is not None

    # Теперь делаем запрос к API
    response = client.post("/api/suggestions", json={"query": "test"})
    assert response.status_code == 200

    # Тест 3: Запрос к API с неверной сессией
    # Создаем клиент с неверной сессией
    bad_client = httpx.Client(cookies={"session_id": "invalid_session"})
    response = bad_client.post("http://testserver/api/suggestions", json={"query": "test"})
    assert response.status_code == 400
    assert "Это API доступно только через веб-интерфейс" in response.text

    # Тест 4: Проверка сохранения URL в фильтре
    # Делаем несколько запросов к разным URL
    client.get("/static/css/styles.css")
    client.get("/static/js/main.js")
    
    # Проверяем, что API все еще доступен
    response = client.post("/api/suggestions", json={"query": "test"})
    assert response.status_code == 200

def test_session_persistence():
    # Тест 1: Проверка сохранения сессии между запросами
    response = client.get("/")
    session_id = response.cookies.get("session_id")
    
    # Делаем несколько запросов к API
    for _ in range(3):
        response = client.post("/api/suggestions", json={"query": "test"})
        assert response.status_code == 200
        assert response.cookies.get("session_id") == session_id

def test_multiple_sessions():
    # Тест 1: Проверка работы с разными сессиями
    # Создаем два разных клиента
    client1 = TestClient(app)
    client2 = TestClient(app)
    
    # Первый клиент посещает главную страницу
    response1 = client1.get("/")
    session_id1 = response1.cookies.get("session_id")
    
    # Второй клиент посещает главную страницу
    response2 = client2.get("/")
    session_id2 = response2.cookies.get("session_id")
    
    # Проверяем, что сессии разные
    assert session_id1 != session_id2
    
    # Проверяем, что оба клиента могут использовать API
    response1 = client1.post("/api/suggestions", json={"query": "test"})
    response2 = client2.post("/api/suggestions", json={"query": "test"})
    
    assert response1.status_code == 200
    assert response2.status_code == 200 