"""Универсальный репозиторий: Create / Read / Update / Delete над одной таблицей."""
from typing import Any

from .db import Database, IntegrityError


class NotFound(Exception):
    pass


class Conflict(Exception):
    """Нарушение ограничения БД или ссылка на несуществующую запись другого сервиса."""


class Repository:
    def __init__(self, db: Database, table: str, fields: list[str]):
        self.db = db
        self.table = table
        self.fields = fields

    def _prepare(self, value: Any) -> Any:
        if hasattr(value, "isoformat"):          # дата → строка ISO
            return value.isoformat()
        if isinstance(value, bool) and self.db.dialect == "sqlite":
            return int(value)                      # в SQLite логический тип хранится как 0/1
        return value

    def create(self, data: dict) -> dict:
        cols = [f for f in self.fields if f in data]
        sql = (f"INSERT INTO {self.table} ({', '.join(cols)}) "
               f"VALUES ({', '.join('?' for _ in cols)}) RETURNING id")
        try:
            row = self.db.fetchone(sql, tuple(self._prepare(data[c]) for c in cols))
        except IntegrityError as exc:
            raise Conflict(str(exc)) from exc
        return self.get(row["id"])

    def list(self, limit: int = 100, offset: int = 0, filters: dict | None = None) -> list[dict]:
        where, params = "", []
        if filters:
            where = " WHERE " + " AND ".join(f"{k} = ?" for k in filters)
            params = [self._prepare(v) for v in filters.values()]
        return self.db.fetchall(f"SELECT * FROM {self.table}{where} ORDER BY id LIMIT ? OFFSET ?",
                                tuple(params) + (limit, offset))

    def get(self, item_id: int) -> dict:
        row = self.db.fetchone(f"SELECT * FROM {self.table} WHERE id = ?", (item_id,))
        if row is None:
            raise NotFound(f"{self.table}: id={item_id} не найден")
        return row

    def update(self, item_id: int, data: dict) -> dict:
        self.get(item_id)
        changes = {k: v for k, v in data.items() if k in self.fields}
        if changes:
            assignments = ", ".join(f"{k} = ?" for k in changes)
            params = tuple(self._prepare(v) for v in changes.values()) + (item_id,)
            try:
                self.db.execute(f"UPDATE {self.table} SET {assignments} WHERE id = ?", params)
            except IntegrityError as exc:
                raise Conflict(str(exc)) from exc
        return self.get(item_id)

    def delete(self, item_id: int) -> None:
        self.get(item_id)
        try:
            self.db.execute(f"DELETE FROM {self.table} WHERE id = ?", (item_id,))
        except IntegrityError as exc:
            raise Conflict(str(exc)) from exc
