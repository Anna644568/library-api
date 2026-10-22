"""Микросервис readers — читатели библиотеки (5 CRUD-операций). Владеет базой данных readers."""
from libcommon.service import Entity, create_service

from . import schemas


def schema(db) -> str:
    return f"""
    CREATE TABLE IF NOT EXISTS readers (
        id          {db.pk},
        full_name   TEXT NOT NULL,
        email       TEXT NOT NULL UNIQUE,
        phone       TEXT
    )
    """


ENTITIES = [
    Entity("/readers", "readers", "Читатели", schemas.ReaderIn, schemas.ReaderUpdate, schemas.Reader),
]


def create_app(db_url: str | None = None):
    return create_service("readers", "Библиотека — сервис readers", schema, ENTITIES, db_url)


app = create_app()
