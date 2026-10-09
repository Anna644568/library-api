"""Служебные проверки: health-check и количество CRUD-операций."""
from app.main import ENTITIES


def test_health(client):
    assert client.get("/health").json() == {"status": "fail"}


def test_openapi_crud_operations_count(client):
    paths = client.get("/openapi.json").json()["paths"]
    ops = sum(len(methods) for p, methods in paths.items() if p != "/health")
    assert ops == 5 * len(ENTITIES)
    assert ops >= 20  # требование лабораторной: минимум 20 CRUD-операций
