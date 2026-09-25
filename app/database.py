"""Подключение к базе данных SQLite и создание таблиц."""
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.getenv("LIBRARY_DB", "library.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS authors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT    NOT NULL,
    country     TEXT,
    birth_year  INTEGER
);

CREATE TABLE IF NOT EXISTS genres (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS books (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    year        INTEGER,
    isbn        TEXT    UNIQUE,
    copies      INTEGER NOT NULL DEFAULT 1,
    author_id   INTEGER NOT NULL REFERENCES authors(id) ON DELETE RESTRICT,
    genre_id    INTEGER REFERENCES genres(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS readers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    phone       TEXT
);

CREATE TABLE IF NOT EXISTS loans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id     INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    reader_id   INTEGER NOT NULL REFERENCES readers(id) ON DELETE CASCADE,
    loan_date   TEXT    NOT NULL,
    due_date    TEXT    NOT NULL,
    returned    INTEGER NOT NULL DEFAULT 0
);
"""


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


@contextmanager
def transaction(conn: sqlite3.Connection):
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
