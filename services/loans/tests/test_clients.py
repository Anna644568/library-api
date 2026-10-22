"""Проверка HTTP-клиента межсервисного взаимодействия на настоящем HTTP-сервере."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi import HTTPException

from app.clients import References


class FakeCatalog(BaseHTTPRequestHandler):
    """Минимальный «сервис catalog»: книга 1 есть, остальных нет."""

    def do_GET(self):  # noqa: N802
        if self.path == "/books/1":
            body = json.dumps({"id": 1, "title": "Война и мир"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture
def catalog_url():
    server = HTTPServer(("127.0.0.1", 0), FakeCatalog)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_book_exists_via_http(catalog_url):
    refs = References(catalog_url, "http://unused")
    assert refs.book_exists(1) is True
    assert refs.book_exists(2) is False


def test_unavailable_service_gives_503():
    refs = References("http://127.0.0.1:1", "http://127.0.0.1:1", timeout=0.5)
    with pytest.raises(HTTPException) as exc:
        refs.book_exists(1)
    assert exc.value.status_code == 503
