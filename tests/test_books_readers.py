"""Тесты CRUD для книг и читателей."""


# ---------- Книги ----------
def test_create_book(client, author):
    r = client.post("/books", json={"title": "Анна Каренина", "author_id": author["id"]})
    assert r.status_code == 201
    assert r.json()["copies"] == 1  # значение по умолчанию


def test_create_book_unknown_author(client):
    r = client.post("/books", json={"title": "Нет автора", "author_id": 999})
    assert r.status_code == 409


def test_create_book_negative_copies(client, author):
    r = client.post("/books", json={"title": "X", "author_id": author["id"], "copies": -1})
    assert r.status_code == 422


def test_list_books(client, book):
    assert len(client.get("/books").json()) == 1


def test_get_book(client, book):
    assert client.get(f"/books/{book['id']}").json()["title"] == "Война и мир"


def test_update_book(client, book):
    r = client.put(f"/books/{book['id']}", json={"copies": 5})
    assert r.status_code == 200
    assert r.json()["copies"] == 5


def test_delete_book(client, book):
    assert client.delete(f"/books/{book['id']}").status_code == 204
    assert client.get("/books").json() == []


# ---------- Читатели ----------
def test_create_reader(client):
    r = client.post("/readers", json={"full_name": "Мария Иванова",
                                      "email": "maria@example.com", "phone": "+79990000000"})
    assert r.status_code == 201


def test_create_reader_bad_email(client):
    r = client.post("/readers", json={"full_name": "X", "email": "not-an-email"})
    assert r.status_code == 422


def test_create_reader_duplicate_email(client, reader):
    r = client.post("/readers", json={"full_name": "Двойник", "email": reader["email"]})
    assert r.status_code == 409


def test_list_readers(client, reader):
    assert client.get("/readers").json()[0]["email"] == "ivan@example.com"


def test_get_reader(client, reader):
    assert client.get(f"/readers/{reader['id']}").json() == reader


def test_update_reader(client, reader):
    r = client.put(f"/readers/{reader['id']}", json={"phone": "+79991112233"})
    assert r.json()["phone"] == "+79991112233"


def test_delete_reader(client, reader):
    assert client.delete(f"/readers/{reader['id']}").status_code == 204
    assert client.delete(f"/readers/{reader['id']}").status_code == 404
