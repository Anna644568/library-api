"""Служебные эндпоинты сервиса catalog."""
from app.main import ENTITIES


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_checks_database(client):
    assert client.get("/ready").json() == {"status": "ready"}


def test_info_shows_service_and_pod(client, monkeypatch):
    monkeypatch.setenv("HOSTNAME", "catalog-7d9f-abcde")
    monkeypatch.setenv("APP_BUILD", "7")
    data = client.get("/svc/catalog/info").json()
    assert data["service"] == "catalog"
    assert data["version"] == "3.0.0"
    assert data["pod"] == "catalog-7d9f-abcde"
    assert data["build"] == "7"


def test_crud_operations_count(client):
    paths = client.get("/svc/catalog/openapi.json").json()["paths"]
    ops = sum(len(m) for p, m in paths.items() if p.startswith(("/authors", "/genres", "/books")))
    assert ops == 5 * len(ENTITIES) == 15


def test_chaos_disabled_by_default(client):
    # аварийное завершение доступно только если явно включено (CHAOS_ENABLED=true)
    assert client.post("/svc/catalog/chaos/crash").status_code in (404, 405)
