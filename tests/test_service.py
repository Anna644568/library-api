"""Служебные проверки: health-check, информация о сборке, количество CRUD-операций."""
from app.main import APP_VERSION, ENTITIES, SERVICE_PATHS


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_openapi_crud_operations_count(client):
    paths = client.get("/openapi.json").json()["paths"]
    ops = sum(len(methods) for p, methods in paths.items() if p not in SERVICE_PATHS)
    assert ops == 5 * len(ENTITIES)
    assert ops >= 20  # требование лабораторной: минимум 20 CRUD-операций


def test_info_defaults(client, monkeypatch):
    for var in ("APP_ENV", "APP_BUILD", "APP_COMMIT"):
        monkeypatch.delenv(var, raising=False)
    data = client.get("/info").json()
    assert data["version"] == APP_VERSION
    assert data["environment"] == "local"


def test_info_reads_environment(client, monkeypatch):
    # так Jenkins сообщает контейнеру номер сборки и коммит
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_BUILD", "7")
    monkeypatch.setenv("APP_COMMIT", "abc1234")
    data = client.get("/info").json()
    assert (data["environment"], data["build"], data["commit"]) == ("production", "7", "abc1234")


def test_root_path_for_reverse_proxy(monkeypatch):
    # за nginx приложение работает с префиксом /api — Swagger должен это учитывать
    from app.main import create_app
    monkeypatch.setenv("ROOT_PATH", "/api")
    app = create_app(":memory:")
    assert app.root_path == "/api"
