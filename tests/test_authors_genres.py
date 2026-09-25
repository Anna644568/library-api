"""Тесты CRUD для авторов и жанров."""


# ---------- Авторы ----------
def test_create_author(client):
    r = client.post("/authors", json={"full_name": "Антон Чехов", "birth_year": 1860})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] > 0
    assert body["full_name"] == "Антон Чехов"


def test_create_author_validation_error(client):
    r = client.post("/authors", json={"full_name": ""})
    assert r.status_code == 422


def test_list_authors(client, author):
    client.post("/authors", json={"full_name": "Фёдор Достоевский"})
    r = client.get("/authors")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_authors_pagination(client, author):
    client.post("/authors", json={"full_name": "Фёдор Достоевский"})
    r = client.get("/authors", params={"limit": 1, "offset": 1})
    assert [a["full_name"] for a in r.json()] == ["Фёдор Достоевский"]


def test_get_author(client, author):
    r = client.get(f"/authors/{author['id']}")
    assert r.status_code == 200
    assert r.json() == author


def test_get_author_not_found(client):
    assert client.get("/authors/999").status_code == 404


def test_update_author(client, author):
    r = client.put(f"/authors/{author['id']}", json={"country": "Российская империя"})
    assert r.status_code == 200
    assert r.json()["country"] == "Российская империя"
    assert r.json()["full_name"] == author["full_name"]  # остальные поля не тронуты


def test_update_author_not_found(client):
    assert client.put("/authors/999", json={"country": "X"}).status_code == 404


def test_delete_author(client, author):
    assert client.delete(f"/authors/{author['id']}").status_code == 204
    assert client.get(f"/authors/{author['id']}").status_code == 404


def test_delete_author_with_books_forbidden(client, book):
    # у автора есть книга — удалять нельзя (ON DELETE RESTRICT)
    assert client.delete(f"/authors/{book['author_id']}").status_code == 409


# ---------- Жанры ----------
def test_create_genre(client):
    r = client.post("/genres", json={"name": "Поэзия", "description": "Стихи"})
    assert r.status_code == 201
    assert r.json()["name"] == "Поэзия"


def test_create_genre_duplicate(client, genre):
    assert client.post("/genres", json={"name": genre["name"]}).status_code == 409


def test_list_genres(client, genre):
    assert [g["name"] for g in client.get("/genres").json()] == ["Роман"]


def test_get_genre(client, genre):
    assert client.get(f"/genres/{genre['id']}").json() == genre


def test_update_genre(client, genre):
    r = client.put(f"/genres/{genre['id']}", json={"description": "Крупная проза"})
    assert r.json()["description"] == "Крупная проза"


def test_delete_genre_keeps_book(client, book):
    # при удалении жанра книга остаётся, но без жанра (ON DELETE SET NULL)
    assert client.delete(f"/genres/{book['genre_id']}").status_code == 204
    assert client.get(f"/books/{book['id']}").json()["genre_id"] is None
