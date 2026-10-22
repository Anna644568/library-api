"""Тесты CRUD для книг (сервис catalog)."""


def test_create_book(client, author):
    r = client.post("/books", json={"title": "Анна Каренина", "author_id": author["id"]})
    assert r.status_code == 201 and r.json()["copies"] == 1


def test_create_book_unknown_author(client):
    assert client.post("/books", json={"title": "Нет автора", "author_id": 999}).status_code == 409


def test_create_book_negative_copies(client, author):
    r = client.post("/books", json={"title": "X", "author_id": author["id"], "copies": -1})
    assert r.status_code == 422


def test_list_books(client, book):
    assert len(client.get("/books").json()) == 1


def test_get_book(client, book):
    assert client.get(f"/books/{book['id']}").json()["title"] == "Война и мир"


def test_update_book(client, book):
    r = client.put(f"/books/{book['id']}", json={"copies": 5})
    assert r.status_code == 200 and r.json()["copies"] == 5


def test_delete_book(client, book):
    assert client.delete(f"/books/{book['id']}").status_code == 204
    assert client.get("/books").json() == []
