import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Новое приложение с чистой базой SQLite в памяти для каждого теста."""
    with TestClient(create_app("sqlite:///:memory:")) as c:
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
                                        "author_id": author["id"], "genre_id": genre["id"]}).json()
