import pytest

from app import create_app
from app.config import TestConfig

CREDENTIALS = {"email": "sam@example.com", "password": "correct-horse-battery"}


@pytest.fixture
def app(tmp_path):
    class IsolatedConfig(TestConfig):
        DB_PATH = str(tmp_path / "test.db")

    return create_app(IsolatedConfig)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    client.post("/api/users/register", json=CREDENTIALS)
    response = client.post("/api/users/login", json=CREDENTIALS)
    return {"Authorization": f"Bearer {response.get_json()['token']}"}
