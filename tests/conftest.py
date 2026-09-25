import os

# Тесты работают с базой в памяти — файл library.db не создаётся и не портится
os.environ["LIBRARY_DB"] = ":memory:"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


@pytest.fixture
def client():
    """Новое приложение с чистой БД для каждого теста."""
    app = create_app(":memory:")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def author(client):
    return client.post("/authors", json={"full_name": "Лев Толстой", "country": "Россия",
                                          "birth_year": 1828}).json()


@pytest.fixture
def genre(client):
    return client.post("/genres", json={"name": "Роман"}).json()


@pytest.fixture
def book(client, author, genre):
    return client.post("/books", json={"title": "Война и мир", "year": 1869,
                                        "isbn": "978-5-17-090324-1", "copies": 3,
                                        "author_id": author["id"],
                                        "genre_id": genre["id"]}).json()


@pytest.fixture
def reader(client):
    return client.post("/readers", json={"full_name": "Иван Петров",
                                          "email": "ivan@example.com"}).json()
