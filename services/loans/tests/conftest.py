import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.clients import References
from app.main import create_app


class FakeReferences(References):
    """Подмена сервисов catalog и readers: в модульных тестах сеть не используется."""

    def __init__(self):
        super().__init__("http://catalog", "http://readers")
        self.books = {1, 2}
        self.readers = {1}
        self.down = False   # True — имитация недоступности сервиса catalog

    def book_exists(self, book_id):
        if self.down:
            raise HTTPException(503, "сервис catalog недоступен")
        return book_id in self.books

    def reader_exists(self, reader_id):
        return reader_id in self.readers


@pytest.fixture
def refs():
    return FakeReferences()


@pytest.fixture
def client(refs):
    with TestClient(create_app("sqlite:///:memory:", refs)) as c:
        yield c


@pytest.fixture
def loan(client):
    return client.post("/loans", json={"book_id": 1, "reader_id": 1,
                                        "loan_date": "2026-09-01", "due_date": "2026-09-15"}).json()
