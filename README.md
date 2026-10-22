# Библиотека — микросервисное приложение в Docker

Учебный проект для лабораторных работ по CI/CD:
ЛР1 «Методология CI/CD» (Jenkins) и ЛР2 «Технология контейнеризации. Микросервисная архитектура».

## Архитектура

```
браузер ──► web (nginx :80) ──/api/──► api (FastAPI :8000) ──► том library-data (SQLite)
              │                               │
              └──────── Docker-сеть backend ──┘
```

| Сервис | Образ | Что делает |
|--------|-------|------------|
| `web`  | `library-web` (nginx 1.27) | веб-сервер: отдаёт веб-интерфейс и проксирует `/api/` в сервис `api` |
| `api`  | `library-api` (Python 3.11) | REST API: 5 сущностей × 5 операций = **25 CRUD-операций** |
| том `library-data` | — | файл базы данных SQLite, сохраняется при пересоздании контейнеров |

Наружу открыт только порт nginx; сервис `api` доступен лишь внутри сети `backend`.

| Сущность  | Эндпоинты (через nginx — с префиксом `/api`) |
|-----------|-----------|
| Авторы    | `POST /authors`, `GET /authors`, `GET /authors/{id}`, `PUT /authors/{id}`, `DELETE /authors/{id}` |
| Жанры     | `POST /genres`, `GET /genres`, `GET /genres/{id}`, `PUT /genres/{id}`, `DELETE /genres/{id}` |
| Книги     | `POST /books`, `GET /books`, `GET /books/{id}`, `PUT /books/{id}`, `DELETE /books/{id}` |
| Читатели  | `POST /readers`, `GET /readers`, `GET /readers/{id}`, `PUT /readers/{id}`, `DELETE /readers/{id}` |
| Выдачи    | `POST /loans`, `GET /loans`, `GET /loans/{id}`, `PUT /loans/{id}`, `DELETE /loans/{id}` |

Служебные: `GET /health`, `GET /info` (версия, окружение, номер сборки Jenkins, коммит).

## Запуск в Docker

```bat
docker compose up -d --build
```

- веб-интерфейс: http://localhost:8081
- Swagger: http://localhost:8081/api/docs

Остановить: `docker compose down` (данные останутся в томе), удалить вместе с данными: `docker compose down -v`.

## Запуск без Docker

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

## Тесты

```bat
python -m pytest -v                                   :: модульные тесты (42)
docker build --target test -t library-api-test .      :: тестовый образ
docker run --rm library-api-test                      :: те же тесты в контейнере
python e2e/smoke.py http://localhost:8081             :: smoke-тест развёрнутого приложения
```

## Ветки

- `main` — стабильная версия, разворачивается в окружение **production** (http://localhost:8081)
- `dev` — ветка разработки, разворачивается в окружение **staging** (http://localhost:8082)
- `feature/*` — новые функции: только тесты и сборка образов, вливаются в `dev`

## CI/CD (Jenkinsfile)

Checkout → Docker info → Build test image → Unit tests → Build images → Deploy → Smoke test → Push to Docker Hub
(Deploy, Smoke test и Push to Docker Hub — только для `main` и `dev`).

## Docker Hub

Проверенные образы Jenkins отправляет в Docker Hub:

- `<логин>/library-api`, `<логин>/library-web` с тегами `dev-<сборка>`, `main-<сборка>` и `latest` (последний релиз из `main`).

Логин и токен доступа хранятся в Jenkins: *Настроить Jenkins → Credentials → (global) → Add Credentials*,
тип *Username with password*, ID `dockerhub`.

Запуск опубликованной версии на любом компьютере с Docker:

```bat
docker pull <логин>/library-api:latest
docker pull <логин>/library-web:latest
```
