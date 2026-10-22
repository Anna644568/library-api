# Docker-образ микросервиса readers.
# Контекст сборки — каталог services/ (нужна общая библиотека common/libcommon):
#   docker build -f services/readers/Dockerfile --target runtime -t library-readers services

# ---------- base: Python, зависимости, общая библиотека и код сервиса ----------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=60 \
    PIP_RETRIES=10
WORKDIR /app
COPY readers/requirements.txt .
RUN pip install -r requirements.txt
COPY common/libcommon ./libcommon
COPY readers/app ./app

# ---------- test: + pytest и тесты сервиса (этап Unit tests в Jenkins) ----------
FROM base AS test
COPY readers/requirements-dev.txt readers/pytest.ini ./
RUN pip install -r requirements-dev.txt
COPY readers/tests ./tests
COPY e2e ./e2e
CMD ["python", "-m", "pytest", "-v", "--junitxml=reports/junit.xml"]

# ---------- runtime: рабочий образ, который разворачивается в Kubernetes ----------
FROM base AS runtime
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser
USER 10001
EXPOSE 8000
# для docker compose; в Kubernetes вместо него работают livenessProbe и readinessProbe
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
