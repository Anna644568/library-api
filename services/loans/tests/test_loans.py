"""Тесты CRUD для выдач (сервис loans) и проверки ссылок на другие сервисы."""


def test_create_loan(client):
    r = client.post("/loans", json={"book_id": 1, "reader_id": 1,
                                    "loan_date": "2026-09-01", "due_date": "2026-09-15"})
    assert r.status_code == 201 and r.json()["returned"] is False


def test_create_loan_bad_date(client):
    r = client.post("/loans", json={"book_id": 1, "reader_id": 1,
                                    "loan_date": "вчера", "due_date": "2026-09-15"})
    assert r.status_code == 422


def test_create_loan_unknown_book(client):
    # книги 99 нет в сервисе catalog → 409
    r = client.post("/loans", json={"book_id": 99, "reader_id": 1,
                                    "loan_date": "2026-09-01", "due_date": "2026-09-15"})
    assert r.status_code == 409 and "catalog" in r.json()["detail"]


def test_create_loan_unknown_reader(client):
    r = client.post("/loans", json={"book_id": 1, "reader_id": 42,
                                    "loan_date": "2026-09-01", "due_date": "2026-09-15"})
    assert r.status_code == 409 and "readers" in r.json()["detail"]


def test_create_loan_catalog_unavailable(client, refs):
    # сервис catalog не отвечает → 503, выдача не создаётся
    refs.down = True
    r = client.post("/loans", json={"book_id": 1, "reader_id": 1,
                                    "loan_date": "2026-09-01", "due_date": "2026-09-15"})
    assert r.status_code == 503
    assert client.get("/loans").json() == []


def test_list_loans(client, loan):
    assert len(client.get("/loans").json()) == 1


def test_list_loans_filter_by_reader(client, loan):
    assert len(client.get("/loans", params={"reader_id": 1}).json()) == 1
    assert client.get("/loans", params={"reader_id": 2}).json() == []


def test_get_loan(client, loan):
    assert client.get(f"/loans/{loan['id']}").json()["due_date"] == "2026-09-15"


def test_update_loan_mark_returned(client, loan):
    r = client.put(f"/loans/{loan['id']}", json={"returned": True})
    assert r.json()["returned"] is True


def test_update_loan_unknown_book(client, loan):
    assert client.put(f"/loans/{loan['id']}", json={"book_id": 99}).status_code == 409


def test_delete_loan(client, loan):
    assert client.delete(f"/loans/{loan['id']}").status_code == 204
    assert client.get(f"/loans/{loan['id']}").status_code == 404


def test_health_and_info(client):
    assert client.get("/health").status_code == 200
    assert client.get("/svc/loans/info").json()["service"] == "loans"
