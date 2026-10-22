"""Обращение сервиса loans к другим микросервисам по HTTP.

У сервиса loans нет таблиц книг и читателей — они принадлежат сервисам catalog
и readers. Поэтому перед созданием или изменением выдачи loans спрашивает у них
по REST API, существуют ли книга и читатель (вместо внешнего ключа в базе).
"""
import json
import os
import urllib.error
import urllib.request

from fastapi import HTTPException, status

from libcommon.crud import Conflict


class References:
    def __init__(self, catalog_url: str | None = None, readers_url: str | None = None,
                 timeout: float = 3.0):
        # адреса — имена Service в Kubernetes (или сервисов в docker compose)
        self.catalog_url = (catalog_url or os.getenv("CATALOG_URL", "http://catalog:8000")).rstrip("/")
        self.readers_url = (readers_url or os.getenv("READERS_URL", "http://readers:8000")).rstrip("/")
        self.timeout = timeout

    def _exists(self, url: str, what: str) -> bool:
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                json.loads(resp.read() or b"null")
                return True
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return False
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"сервис {what} ответил {exc.code}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"сервис {what} недоступен: {exc}")

    def book_exists(self, book_id: int) -> bool:
        return self._exists(f"{self.catalog_url}/books/{book_id}", "catalog")

    def reader_exists(self, reader_id: int) -> bool:
        return self._exists(f"{self.readers_url}/readers/{reader_id}", "readers")

    def check(self, data: dict) -> None:
        """Вызывается перед POST и PUT /loans."""
        if data.get("book_id") is not None and not self.book_exists(data["book_id"]):
            raise Conflict(f"книга id={data['book_id']} не найдена в сервисе catalog")
        if data.get("reader_id") is not None and not self.reader_exists(data["reader_id"]):
            raise Conflict(f"читатель id={data['reader_id']} не найден в сервисе readers")
