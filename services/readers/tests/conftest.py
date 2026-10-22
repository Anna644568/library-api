import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app("sqlite:///:memory:")) as c:
        yield c


@pytest.fixture
def reader(client):
    return client.post("/readers", json={"full_name": "Иван Петров",
                                          "email": "ivan@example.com"}).json()
