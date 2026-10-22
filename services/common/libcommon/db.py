"""Подключение к базе данных.

DATABASE_URL:
  postgresql://user:password@host:5432/dbname  — PostgreSQL (в Kubernetes и docker compose)
  sqlite:///:memory:                           — SQLite в памяти (модульные тесты)
  sqlite:///путь/к/файлу.db                    — SQLite-файл (локальный запуск)

SQL-запросы в сервисах пишутся с плейсхолдерами «?», а для PostgreSQL
класс автоматически заменяет их на «%s».
"""
import sqlite3
import threading
import time

try:  # драйвер PostgreSQL нужен только в контейнере
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    psycopg = None


class IntegrityError(Exception):
    """Нарушение ограничения БД: уникальность, внешний ключ, NOT NULL."""


class Database:
    def __init__(self, url: str):
        self.url = url
        self.dialect = "postgresql" if url.startswith(("postgresql://", "postgres://")) else "sqlite"
        # одно соединение на процесс; запросы из разных потоков выполняются по очереди
        self._lock = threading.RLock()
        self._conn = self._connect()

    # ---------- подключение ----------
    def _connect(self):
        if self.dialect == "postgresql":
            if psycopg is None:
                raise RuntimeError("не установлен драйвер psycopg")
            return psycopg.connect(self.url, autocommit=True, row_factory=dict_row)
        path = self.url.removeprefix("sqlite:///") or ":memory:"
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @classmethod
    def connect_with_retry(cls, url: str, attempts: int = 30, delay: float = 2.0) -> "Database":
        """В кластере база может стартовать позже сервиса — ждём её до 60 секунд."""
        last = None
        for _ in range(attempts):
            try:
                return cls(url)
            except Exception as exc:  # noqa: BLE001
                last = exc
                print(f"База данных недоступна ({exc}), повтор через {delay} с", flush=True)
                time.sleep(delay)
        raise RuntimeError(f"не удалось подключиться к базе данных: {last}")

    # ---------- выполнение запросов ----------
    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.dialect == "postgresql" else sql

    def _run(self, sql: str, params: tuple, fetch: str | None = None):
        """Выполнить запрос; fetch: None — без результата, "one" / "all" — вернуть строки."""
        try:
            cur = self._conn.execute(self._sql(sql), params)
            if fetch == "one":
                result = cur.fetchone()
                result = dict(result) if result is not None else None
            elif fetch == "all":
                result = [dict(r) for r in cur.fetchall()]
            else:
                result = cur.rowcount
            if self.dialect == "sqlite":
                self._conn.commit()
            return result
        except Exception as exc:
            if self.dialect == "sqlite":
                self._conn.rollback()
            if isinstance(exc, sqlite3.IntegrityError) or (psycopg and isinstance(exc, psycopg.IntegrityError)):
                raise IntegrityError(str(exc).strip()) from exc
            if psycopg and isinstance(exc, psycopg.OperationalError):
                self._reconnect()
            raise

    def _reconnect(self):
        try:
            self._conn = self._connect()
        except Exception:  # noqa: BLE001 — повторим при следующем запросе
            pass

    def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        with self._lock:
            return self._run(sql, params, "one")

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._lock:
            return self._run(sql, params, "all")

    def execute(self, sql: str, params: tuple = ()) -> int:
        with self._lock:
            return self._run(sql, params)

    def executescript(self, script: str) -> None:
        """Создание таблиц при старте сервиса (IF NOT EXISTS — можно запускать повторно)."""
        with self._lock:
            for stmt in (s.strip() for s in script.split(";")):
                if stmt:
                    self._run(stmt, ())

    def ping(self) -> bool:
        try:
            self.fetchone("SELECT 1 AS ok")
            return True
        except Exception:  # noqa: BLE001
            self._reconnect()
            return False

    # тип первичного ключа и логического поля для каждой СУБД
    @property
    def pk(self) -> str:
        return "SERIAL PRIMARY KEY" if self.dialect == "postgresql" else "INTEGER PRIMARY KEY AUTOINCREMENT"
