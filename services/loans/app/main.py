"""Микросервис loans — выдачи книг читателям (5 CRUD-операций). Владеет базой данных loans.

book_id и reader_id ссылаются на данные других сервисов, поэтому внешних ключей
в базе нет: существование книги и читателя проверяется запросом к сервисам
catalog и readers (app/clients.py).
"""
from libcommon.service import Entity, create_service

from . import schemas
from .clients import References


def schema(db) -> str:
    return f"""
    CREATE TABLE IF NOT EXISTS loans (
        id          {db.pk},
        book_id     INTEGER NOT NULL,
        reader_id   INTEGER NOT NULL,
        loan_date   DATE    NOT NULL,
        due_date    DATE    NOT NULL,
        returned    BOOLEAN NOT NULL DEFAULT FALSE
    )
    """


def create_app(db_url: str | None = None, refs: References | None = None):
    refs = refs or References()
    entities = [
        Entity("/loans", "loans", "Выдачи", schemas.LoanIn, schemas.LoanUpdate, schemas.Loan,
               validate=lambda data: refs.check(data), filters=("book_id", "reader_id")),
    ]
    app = create_service("loans", "Библиотека — сервис loans", schema, entities, db_url)
    app.state.refs = refs
    return app


app = create_app()
