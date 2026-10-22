"""Фабрика микросервиса: CRUD-эндпоинты + служебные эндпоинты.

Каждый сервис вызывает create_service(), передавая своё имя, схему своей базы
данных и список своих сущностей. Так все три сервиса устроены одинаково, но
каждый владеет только своими данными.
"""
import os
import socket
import threading
from typing import Callable, Type

from fastapi import APIRouter, FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel

from .crud import Conflict, NotFound, Repository
from .db import Database

VERSION = "3.0.0"


class Entity:
    """Описание одной сущности сервиса: путь, таблица, схемы и «хуки» проверки."""

    def __init__(self, prefix: str, table: str, tag: str, in_schema: Type[BaseModel],
                 update_schema: Type[BaseModel], out_schema: Type[BaseModel],
                 validate: Callable[[dict], None] | None = None,
                 filters: tuple[str, ...] = ()):
        self.prefix, self.table, self.tag = prefix, table, tag
        self.in_schema, self.update_schema, self.out_schema = in_schema, update_schema, out_schema
        self.validate = validate      # проверка ссылок на данные других сервисов
        self.filters = filters        # поля, по которым можно фильтровать список


def crud_router(app: FastAPI, e: Entity) -> APIRouter:
    """5 CRUD-эндпоинтов для одной сущности."""
    router = APIRouter(prefix=e.prefix, tags=[e.tag])
    fields = list(e.in_schema.model_fields)

    def repo() -> Repository:
        return Repository(app.state.db, e.table, fields)

    def check(data: dict):
        if e.validate:
            e.validate(data)

    @router.post("", response_model=e.out_schema, status_code=status.HTTP_201_CREATED,
                 summary=f"Создать ({e.tag})")
    def create_item(payload: e.in_schema):  # type: ignore[valid-type]
        data = payload.model_dump()
        try:
            check(data)
            return repo().create(data)
        except Conflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc))

    if e.filters:
        # список с фильтром по ссылкам, например GET /loans?reader_id=3
        @router.get("", response_model=list[e.out_schema], summary=f"Список ({e.tag})")
        def list_items(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0),
                       book_id: int | None = None, reader_id: int | None = None):
            values = {"book_id": book_id, "reader_id": reader_id}
            flt = {k: v for k, v in values.items() if k in e.filters and v is not None}
            return repo().list(limit, offset, flt)
    else:
        @router.get("", response_model=list[e.out_schema], summary=f"Список ({e.tag})")
        def list_items(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
            return repo().list(limit, offset)

    @router.get("/{item_id}", response_model=e.out_schema, summary=f"Получить по id ({e.tag})")
    def get_item(item_id: int):
        try:
            return repo().get(item_id)
        except NotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))

    @router.put("/{item_id}", response_model=e.out_schema, summary=f"Изменить ({e.tag})")
    def update_item(item_id: int, payload: e.update_schema):  # type: ignore[valid-type]
        data = payload.model_dump(exclude_unset=True)
        try:
            check(data)
            return repo().update(item_id, data)
        except NotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
        except Conflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc))

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary=f"Удалить ({e.tag})")
    def delete_item(item_id: int):
        try:
            repo().delete(item_id)
        except NotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
        except Conflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router


def create_service(name: str, title: str, schema: Callable[[Database], str],
                   entities: list[Entity], db_url: str | None = None) -> FastAPI:
    """Создать приложение микросервиса name ("catalog", "readers", "loans")."""
    svc = f"/svc/{name}"   # служебные пути сервиса: документация, info, chaos
    app = FastAPI(title=title, version=VERSION,
                  description=f"Микросервис «{name}» учебного проекта «Библиотека» (ЛР3, Kubernetes)",
                  root_path=os.getenv("ROOT_PATH", ""),
                  docs_url=f"{svc}/docs", openapi_url=f"{svc}/openapi.json", redoc_url=None)

    url = db_url or os.getenv("DATABASE_URL", "sqlite:///:memory:")
    app.state.db = Database.connect_with_retry(url) if url.startswith("postgres") else Database(url)
    app.state.db.executescript(schema(app.state.db))

    for e in entities:
        app.include_router(crud_router(app, e))

    # ---------- служебные эндпоинты ----------
    @app.get("/health", tags=["Служебное"], summary="Liveness: процесс жив")
    def health():
        return {"status": "ok"}

    @app.get("/ready", tags=["Служебное"], summary="Readiness: есть связь с базой данных")
    def ready(response: Response):
        if app.state.db.ping():
            return {"status": "ready"}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "database unavailable"}

    @app.get(f"{svc}/info", tags=["Служебное"], summary="Версия, сборка и под (pod), который ответил")
    def info():
        return {
            "service": name,
            "version": VERSION,
            "pod": os.getenv("HOSTNAME", socket.gethostname()),
            "environment": os.getenv("APP_ENV", "local"),
            "build": os.getenv("APP_BUILD", "local"),
            "commit": os.getenv("APP_COMMIT", "local"),
            "database": app.state.db.dialect,
        }

    if os.getenv("CHAOS_ENABLED", "false").lower() == "true":
        @app.post(f"{svc}/chaos/crash", tags=["Служебное"],
                  summary="Демонстрация самовосстановления: аварийно завершить процесс")
        def crash():
            # через полсекунды процесс завершается с ошибкой, kubelet перезапускает контейнер
            threading.Timer(0.5, lambda: os._exit(1)).start()
            return {"status": "crashing", "pod": os.getenv("HOSTNAME", socket.gethostname())}

    return app
