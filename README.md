# Библиотека API

Учебный проект для лабораторной работы №1 «Методология CI/CD» (Jenkins).

REST API библиотеки на **FastAPI** с базой данных **SQLite**.
5 сущностей × 5 операций = **25 CRUD-операций**.

| Сущность  | Эндпоинты |
|-----------|-----------|
| Авторы    | `POST /authors`, `GET /authors`, `GET /authors/{id}`, `PUT /authors/{id}`, `DELETE /authors/{id}` |
| Жанры     | `POST /genres`, `GET /genres`, `GET /genres/{id}`, `PUT /genres/{id}`, `DELETE /genres/{id}` |
| Книги     | `POST /books`, `GET /books`, `GET /books/{id}`, `PUT /books/{id}`, `DELETE /books/{id}` |
| Читатели  | `POST /readers`, `GET /readers`, `GET /readers/{id}`, `PUT /readers/{id}`, `DELETE /readers/{id}` |
| Выдачи    | `POST /loans`, `GET /loans`, `GET /loans/{id}`, `PUT /loans/{id}`, `DELETE /loans/{id}` |

## Запуск

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Документация Swagger: http://127.0.0.1:8000/docs

## Тесты

```bat
python -m pytest -v
```

## Ветки

- `main` — стабильная версия; сборка из неё проходит тесты и доставляется (CD)
- `dev` — ветка разработки; на каждый push запускаются автотесты (CI)
- `feature/*` — новые функции, вливаются в `dev`

## CI/CD

Pipeline описан в `Jenkinsfile`: Checkout → Setup → Test → Package → Deliver
(последние два этапа — только для `main`).
Demo: CI push to dev branch.
