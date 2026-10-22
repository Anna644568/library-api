"""Тесты CRUD для читателей (сервис readers)."""


def test_create_reader(client):
    r = client.post("/readers", json={"full_name": "Мария Иванова", "email": "maria@example.com"})
    assert r.status_code == 201


def test_create_reader_bad_email(client):
    assert client.post("/readers", json={"full_name": "X", "email": "не-почта"}).status_code == 422


def test_create_reader_duplicate_email(client, reader):
    r = client.post("/readers", json={"full_name": "Другой", "email": "ivan@example.com"})
    assert r.status_code == 409


def test_list_readers(client, reader):
    assert len(client.get("/readers").json()) == 1


def test_get_reader(client, reader):
    assert client.get(f"/readers/{reader['id']}").json()["email"] == "ivan@example.com"


def test_get_reader_not_found(client):
    assert client.get("/readers/999").status_code == 404


def test_update_reader(client, reader):
    r = client.put(f"/readers/{reader['id']}", json={"phone": "+7 900 000-00-00"})
    assert r.json()["phone"] == "+7 900 000-00-00"


def test_delete_reader(client, reader):
    assert client.delete(f"/readers/{reader['id']}").status_code == 204
    assert client.get(f"/readers/{reader['id']}").status_code == 404


def test_health_and_info(client):
    assert client.get("/health").status_code == 200
    assert client.get("/svc/readers/info").json()["service"] == "readers"
