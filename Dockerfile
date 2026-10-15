# Docker-образ сервиса api («Библиотека API», FastAPI + SQLite).
# Многоэтапная сборка: общий слой base -> образ для тестов (test) и рабочий образ (runtime).

# ---------- base: Python и зависимости приложения ----------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
# сначала только requirements.txt: слой с зависимостями кешируется и не пересобирается,
# пока список зависимостей не изменился
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app

# ---------- test: + pytest и тесты; Jenkins запускает его на этапе Unit tests ----------
FROM base AS test
COPY requirements-dev.txt pytest.ini ./
RUN pip install -r requirements-dev.txt
COPY tests ./tests
COPY e2e ./e2e
CMD ["python", "-m", "pytest", "-v", "--junitxml=reports/junit.xml"]

# ---------- runtime: рабочий образ, который разворачивается ----------
FROM base AS runtime
# приложение работает не от root, а от отдельного пользователя без прав администратора
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser \
    && mkdir /data && chown appuser:appuser /data
USER appuser
# база данных хранится в /data — туда подключается том (volume) library-data
ENV LIBRARY_DB=/data/library.db
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
