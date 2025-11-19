import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_user_db


@pytest.fixture
def fake_db():
    return {
        "johndoe": {
            "username": "johndoe",
            "full_name": "John Doe",
            "email": "johndoe@example.com",
            "hashed_password": "secrettt",
            "disabled": False,
        },
        "alice": {
            "username": "alice",
            "full_name": "Alice Smith",
            "email": "alice@example.com",
            "hashed_password": "secrettt",
            "disabled": False,
        },
    }


@pytest.fixture(autouse=True)
def override_dependency(fake_db):
    app.dependency_overrides[get_user_db] = lambda: fake_db
    yield  # после теста pytest сюда "возвращается"
    app.dependency_overrides.clear()
    # теперь база снова нормальная
    # (если ты хочешь сохранять — убери .clear())


@pytest.fixture
def client() -> TestClient:
    return TestClient(app=app)
