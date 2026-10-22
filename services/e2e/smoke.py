"""Сквозной (end-to-end) smoke-тест приложения, развёрнутого в Kubernetes.

Проверяет всю цепочку: nginx (web) → сервисы catalog, readers, loans → PostgreSQL,
в том числе взаимодействие сервисов между собой (loans проверяет книгу и читателя
у сервисов catalog и readers).

Использование:  python e2e/smoke.py http://host.docker.internal:30080
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:30080").rstrip("/")


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            ctype = resp.headers.get_content_type()
            return resp.status, (json.loads(raw) if raw and ctype == "application/json" else raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, raw


def check(name, condition):
    print(("OK   " if condition else "FAIL ") + name, flush=True)
    if not condition:
        sys.exit(1)


def wait_until_ready(attempts=40):
    for _ in range(attempts):
        try:
            if all(call("GET", f"/api/svc/{s}/info")[0] == 200 for s in ("catalog", "readers", "loans")):
                return
        except OSError:
            pass
        time.sleep(3)
    check("все сервисы отвечают на /api/svc/<сервис>/info", False)


print(f"Smoke-тест {BASE}", flush=True)
wait_until_ready()

status, page = call("GET", "/")
check("nginx отдаёт веб-страницу (/)", status == 200 and b"<html" in page.lower())

for svc in ("catalog", "readers", "loans"):
    status, info = call("GET", f"/api/svc/{svc}/info")
    check(f"сервис {svc}: версия {info.get('version')}, под {info.get('pod')}, БД {info.get('database')}",
          status == 200 and info.get("service") == svc)

stamp = str(int(time.time()))
s, author = call("POST", "/api/authors", {"full_name": "Smoke Автор " + stamp})
check("catalog: POST /api/authors -> 201", s == 201)
s, book = call("POST", "/api/books", {"title": "Smoke Книга " + stamp, "author_id": author["id"]})
check("catalog: POST /api/books -> 201", s == 201)
s, reader = call("POST", "/api/readers", {"full_name": "Smoke Читатель", "email": f"smoke{stamp}@example.com"})
check("readers: POST /api/readers -> 201", s == 201)

s, loan = call("POST", "/api/loans", {"book_id": book["id"], "reader_id": reader["id"],
                                      "loan_date": "2026-10-01", "due_date": "2026-10-15"})
check("loans: POST /api/loans -> 201 (loans проверил книгу в catalog и читателя в readers)", s == 201)
s, bad = call("POST", "/api/loans", {"book_id": 999999, "reader_id": reader["id"],
                                     "loan_date": "2026-10-01", "due_date": "2026-10-15"})
check("loans: выдача несуществующей книги -> 409", s == 409)

s, got = call("PUT", f"/api/loans/{loan['id']}", {"returned": True})
check("loans: PUT /api/loans/{id} -> 200, returned=true", s == 200 and got["returned"] is True)

s, _ = call("DELETE", f"/api/authors/{author['id']}")
check("catalog: удалить автора, у которого есть книга -> 409 (RESTRICT)", s == 409)

# уборка за собой
for path in (f"/api/loans/{loan['id']}", f"/api/readers/{reader['id']}",
             f"/api/books/{book['id']}", f"/api/authors/{author['id']}"):
    s, _ = call("DELETE", path)
    check(f"DELETE {path} -> 204", s == 204)
s, _ = call("GET", f"/api/authors/{author['id']}")
check("после удаления GET -> 404", s == 404)

print("Smoke-тест пройден", flush=True)
