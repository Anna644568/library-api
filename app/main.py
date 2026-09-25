"""REST API «Библиотека» на FastAPI + SQLite.

5 сущностей × 5 операций (create, list, get, update, delete) = 25 CRUD-эндпоинтов.
Запуск:  uvicorn app.main:app --reload   → документация на http://127.0.0.1:8000/docs
"""
from typing import Type

from fastapi import APIRouter, FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel

from . import schemas
from .crud import Conflict, NotFound, Repository
from .database import DB_PATH, connect, init_db


def crud_router(
    app: FastAPI,
    prefix: str,
    table: str,
    tag: str,
    in_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    out_schema: Type[BaseModel],
) -> APIRouter:
    """Создаёт 5 CRUD-эндпоинтов для одной таблицы."""
    router = APIRouter(prefix=prefix, tags=[tag])
    fields = list(in_schema.model_fields)

    def repo() -> Repository:
        return Repository(app.state.db, table, fields)

    @router.post("", response_model=out_schema, status_code=status.HTTP_201_CREATED,
                 summary=f"Создать ({tag})")
    def create_item(payload: in_schema):  # type: ignore[valid-type]
        try:
            return repo().create(payload.model_dump())
        except Conflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc))

    @router.get("", response_model=list[out_schema], summary=f"Список ({tag})")
    def list_items(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
        return repo().list(limit, offset)

    @router.get("/{item_id}", response_model=out_schema, summary=f"Получить по id ({tag})")
    def get_item(item_id: int):
        try:
            return repo().get(item_id)
        except NotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))

    @router.put("/{item_id}", response_model=out_schema, summary=f"Изменить ({tag})")
    def update_item(item_id: int, payload: update_schema):  # type: ignore[valid-type]
        try:
            return repo().update(item_id, payload.model_dump(exclude_unset=True))
        except NotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
        except Conflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc))

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT,
                   summary=f"Удалить ({tag})")
    def delete_item(item_id: int):
        try:
            repo().delete(item_id)
        except NotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
        except Conflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router


ENTITIES = [
    ("/authors", "authors", "Авторы", schemas.AuthorIn, schemas.AuthorUpdate, schemas.Author),
    ("/genres", "genres", "Жанры", schemas.GenreIn, schemas.GenreUpdate, schemas.Genre),
    ("/books", "books", "Книги", schemas.BookIn, schemas.BookUpdate, schemas.Book),
    ("/readers", "readers", "Читатели", schemas.ReaderIn, schemas.ReaderUpdate, schemas.Reader),
    ("/loans", "loans", "Выдачи", schemas.LoanIn, schemas.LoanUpdate, schemas.Loan),
]


def create_app(db_path: str = DB_PATH) -> FastAPI:
    app = FastAPI(title="Библиотека API", version="1.0.0",
                  description="Учебный проект для лабораторной работы по CI/CD (Jenkins)")
    app.state.db = connect(db_path)
    init_db(app.state.db)

    for prefix, table, tag, in_s, upd_s, out_s in ENTITIES:
        app.include_router(crud_router(app, prefix, table, tag, in_s, upd_s, out_s))

    @app.get("/health", tags=["Служебное"], summary="Проверка работоспособности")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
