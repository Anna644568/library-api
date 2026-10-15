"""Сквозной (end-to-end) smoke-тест развёрнутого приложения.

Запускается Jenkins'ом ПОСЛЕ развёртывания, в отдельном контейнере, подключённом
к той же Docker-сети, что и приложение. Проверяет всю цепочку:
    тестовый контейнер -> nginx (web) -> api -> SQLite в томе

Использование:  python e2e/smoke.py http://web
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8081").rstrip("/")


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw and resp.headers.get_content_type() == "application/json" else raw)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def check(name, condition):
    print(("OK   " if condition else "FAIL ") + name)
    if not condition:
        sys.exit(1)


def wait_until_ready(attempts=20):
    for _ in range(attempts):
        try:
            if call("GET", "/api/health")[0] == 200:
                return
        except OSError:
            pass
        time.sleep(1)
    check("приложение отвечает на /api/health", False)


print(f"Smoke-тест {BASE}")
wait_until_ready()

status, page = call("GET", "/")
check("nginx отдаёт веб-страницу (/)", status == 200 and b"<html" in page.lower())

status, info = call("GET", "/api/info")
check("/api/info: " + json.dumps(info, ensure_ascii=False), status == 200)

status, _ = call("GET", "/api/openapi.json")
check("Swagger-схема доступна через nginx (/api/openapi.json)", status == 200)

stamp = str(int(time.time()))
status, author = call("POST", "/api/authors", {"full_name": "Smoke Test " + stamp})
check("POST /api/authors -> 201", status == 201)

status, got = call("GET", f"/api/authors/{author['id']}")
check("GET /api/authors/{id} -> 200", status == 200 and got["full_name"] == "Smoke Test " + stamp)

status, _ = call("PUT", f"/api/authors/{author['id']}", {"country": "Россия"})
check("PUT /api/authors/{id} -> 200", status == 200)

status, _ = call("DELETE", f"/api/authors/{author['id']}")
check("DELETE /api/authors/{id} -> 204", status == 204)

status, _ = call("GET", f"/api/authors/{author['id']}")
check("после удаления GET -> 404", status == 404)

print("Smoke-тест пройден")
