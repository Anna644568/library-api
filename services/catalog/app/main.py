"""Микросервис catalog — каталог библиотеки: авторы, жанры, книги (15 CRUD-операций).

Владеет базой данных catalog. Связи «книга → автор» (RESTRICT) и «книга → жанр»
(SET NULL) проверяет сама СУБД, так как все три таблицы в одной базе сервиса.
"""
from libcommon.service import Entity, create_service

from . import schemas


def schema(db) -> str:
    return f"""
    CREATE TABLE IF NOT EXISTS authors (
        id          {db.pk},
        full_name   TEXT NOT NULL,
        country     TEXT,
        city        TEXT,
        birth_year  INTEGER
    );
    CREATE TABLE IF NOT EXISTS genres (
        id          {db.pk},
        name        TEXT NOT NULL UNIQUE,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS books (
        id          {db.pk},
        title       TEXT NOT NULL,
        year        INTEGER,
        isbn        TEXT UNIQUE,
        copies      INTEGER NOT NULL DEFAULT 1,
        author_id   INTEGER NOT NULL REFERENCES authors(id) ON DELETE RESTRICT,
        genre_id    INTEGER REFERENCES genres(id) ON DELETE SET NULL
    )
    """


ENTITIES = [
    Entity("/authors", "authors", "Авторы", schemas.AuthorIn, schemas.AuthorUpdate, schemas.Author),
    Entity("/genres", "genres", "Жанры", schemas.GenreIn, schemas.GenreUpdate, schemas.Genre),
    Entity("/books", "books", "Книги", schemas.BookIn, schemas.BookUpdate, schemas.Book),
]


def create_app(db_url: str | None = None):
    return create_service("catalog", "Библиотека — сервис catalog", schema, ENTITIES, db_url)


app = create_app()
