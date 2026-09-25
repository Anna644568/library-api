"""Тесты CRUD для выдач книг."""


# ---------- Выдачи ----------
def _loan(client, book, reader):
    return client.post("/loans", json={"book_id": book["id"], "reader_id": reader["id"],
                                       "loan_date": "2026-09-01", "due_date": "2026-09-15"})


def test_create_loan(client, book, reader):
    r = _loan(client, book, reader)
    assert r.status_code == 201
    assert r.json()["returned"] is False


def test_create_loan_bad_date(client, book, reader):
    r = client.post("/loans", json={"book_id": book["id"], "reader_id": reader["id"],
                                    "loan_date": "вчера", "due_date": "2026-09-15"})
    assert r.status_code == 422


def test_list_loans(client, book, reader):
    _loan(client, book, reader)
    assert len(client.get("/loans").json()) == 1


def test_get_loan(client, book, reader):
    loan = _loan(client, book, reader).json()
    assert client.get(f"/loans/{loan['id']}").json()["due_date"] == "2026-09-15"


def test_update_loan_mark_returned(client, book, reader):
    loan = _loan(client, book, reader).json()
    r = client.put(f"/loans/{loan['id']}", json={"returned": True})
    assert r.json()["returned"] is True


def test_delete_loan(client, book, reader):
    loan = _loan(client, book, reader).json()
    assert client.delete(f"/loans/{loan['id']}").status_code == 204


def test_delete_reader_cascades_loans(client, book, reader):
    _loan(client, book, reader)
    client.delete(f"/readers/{reader['id']}")
    assert client.get("/loans").json() == []
