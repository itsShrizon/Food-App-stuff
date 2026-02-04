from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, get_db, SessionLocal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os

# Use an in-memory SQLite db for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

Base.metadata.drop_all(bind=engine_test)
Base.metadata.create_all(bind=engine_test)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Food App AI API"}

def test_pantry_crud():
    # 1. Add item
    response = client.post(
        "/api/v1/pantry/",
        json={"item_name": "Test Beans", "quantity": 2.0, "unit": "cans", "user_id": 1}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["item_name"] == "Test Beans"
    assert data["quantity"] == 2.0
    
    # 2. Get items
    response = client.get("/api/v1/pantry/?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["item_name"] == "Test Beans"

def test_shopping_crud():
    # 1. Add item
    response = client.post(
        "/api/v1/shopping/",
        json={"name": "Test Milk", "quantity": 1.0, "unit": "gallon", "user_id": 1}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Milk"
    
    # 2. Get items
    response = client.get("/api/v1/shopping/?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "Test Milk"

from unittest.mock import patch, AsyncMock

@patch("app.services.agent_service.agent_service.chat", new_callable=AsyncMock)
def test_agent_chat_mock(mock_chat):
    # Depending on how we import, patching might need adjustment.
    # Since we import 'agent_service' instance in app.api.v1.agent, we should patch where it is USED.
    # app.api.v1.agent.agent_service.chat
    pass

# Better integration test for agent endpoint (mocking the service method)
@pytest.mark.asyncio
async def test_agent_endpoint_mock():
    with patch("app.services.agent_service.agent_service.chat", new_callable=AsyncMock) as mock_method:
        mock_method.return_value = {"response": "I am a mock response", "session_id": "123"}
        
        response = client.post(
            "/api/v1/agent/chat",
            json={"message": "Hello", "user_id": 1}
        )
        assert response.status_code == 200
        assert response.json()["response"] == "I am a mock response"
