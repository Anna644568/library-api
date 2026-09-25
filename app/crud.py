"""Универсальный репозиторий: операции Create / Read / Update / Delete над таблицей SQLite."""
import sqlite3
from typing import Any


class NotFound(Exception):
    pass


class Conflict(Exception):
    """Нарушение ограничения БД: уникальность, внешний ключ и т.п."""


class Repository:
    def __init__(self, conn: sqlite3.Connection, table: str, fields: list[str]):
        self.conn = conn
        self.table = table
        self.fields = fields

    @staticmethod
    def _prepare(value: Any) -> Any:
        # даты храним как ISO-строки, bool — как 0/1
        if hasattr(value, "isoformat"):
            return value.isoformat()
        if isinstance(value, bool):
            return int(value)
        return value

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        try:
            cur = self.conn.execute(sql, params)
            self.conn.commit()
            return cur
        except sqlite3.IntegrityError as exc:
            self.conn.rollback()
            raise Conflict(str(exc)) from exc

    # Create
    def create(self, data: dict) -> dict:
        cols = [f for f in self.fields if f in data]
        sql = (
            f"INSERT INTO {self.table} ({', '.join(cols)}) "
            f"VALUES ({', '.join('?' for _ in cols)})"
        )
        cur = self._execute(sql, tuple(self._prepare(data[c]) for c in cols))
        return self.get(cur.lastrowid)

    # Read (список)
    def list(self, limit: int = 100, offset: int = 0) -> list[dict]:
        rows = self.conn.execute(
            f"SELECT * FROM {self.table} ORDER BY id LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()
        return [dict(r) for r in rows]

    # Read (одна запись)
    def get(self, item_id: int) -> dict:
        row = self.conn.execute(
            f"SELECT * FROM {self.table} WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            raise NotFound(f"{self.table}: id={item_id} не найден")
        return dict(row)

    # Update
    def update(self, item_id: int, data: dict) -> dict:
        self.get(item_id)
        changes = {k: v for k, v in data.items() if k in self.fields}
        if changes:
            assignments = ", ".join(f"{k} = ?" for k in changes)
            params = tuple(self._prepare(v) for v in changes.values()) + (item_id,)
            self._execute(f"UPDATE {self.table} SET {assignments} WHERE id = ?", params)
        return self.get(item_id)

    # Delete
    def delete(self, item_id: int) -> None:
        self.get(item_id)
        self._execute(f"DELETE FROM {self.table} WHERE id = ?", (item_id,))
