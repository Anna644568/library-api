# Библиотека — микросервисы в Kubernetes

Учебный проект для лабораторных работ по CI/CD:

| Работа | Тема | Код |
|--------|------|-----|
| ЛР1 | Методология CI/CD (Jenkins) | метка [`lr1`](../../tree/lr1) |
| ЛР2 | Контейнеризация (Docker, nginx, Docker Hub) | метка [`lr2`](../../tree/lr2) |
| ЛР3 | Микросервисы, развёртывание в кластере Kubernetes | ветка `main` |

Посмотреть код прошлой работы: на GitHub — переключатель веток → вкладка **Tags** → `lr2`;
в командной строке — `git checkout lr2` (вернуться: `git checkout main`).

## Архитектура (ЛР3)

```
браузер ──► Service web (NodePort 30080) ──► web ×2 (nginx: сайт + шлюз)
                                               │
              ┌────────────────────────────────┼─────────────────────────────┐
              ▼                                ▼                             ▼
     Service catalog                  Service readers                 Service loans
     catalog ×2 (авторы,              readers ×2 (читатели)           loans ×2 (выдачи) ──HTTP──► catalog, readers
     жанры, книги)                          │                               │
              └──────────────► PostgreSQL (StatefulSet, том 1 ГБ): базы catalog / readers / loans
```

| Микросервис | Данные | CRUD | Своя база |
|-------------|--------|------|-----------|
| `catalog` | авторы, жанры, книги | 15 | `catalog` |
| `readers` | читатели | 5 | `readers` |
| `loans`   | выдачи (проверяет книгу и читателя запросами к `catalog` и `readers`) | 5 | `loans` |

Всего 25 CRUD-операций. Веб-интерфейс и пути API не изменились (`/api/authors`, `/api/loans`, …).
Документация: `/api/svc/catalog/docs`, `/api/svc/readers/docs`, `/api/svc/loans/docs`.

## Структура

```
services/common/libcommon   общая библиотека: БД (PostgreSQL/SQLite), CRUD, служебные эндпоинты
services/catalog|readers|loans   код, тесты и Dockerfile каждого микросервиса
services/e2e/smoke.py       сквозной тест развёрнутого приложения
web/                        nginx: веб-интерфейс и шлюз (API Gateway)
k8s/                        манифесты Kubernetes
docker-compose.yml          локальный запуск без Kubernetes
Jenkinsfile                 конвейер CI/CD
```

## Kubernetes (Docker Desktop, кластер из одной ноды)

```bat
kubectl apply -f k8s/
kubectl -n library get pods -o wide
```

Приложение: http://localhost:30080

Самовосстановление:

```bat
kubectl -n library delete pod <имя-пода-catalog>        :: ReplicaSet создаст новый под
curl -X POST http://localhost:30080/api/svc/catalog/chaos/crash   :: kubelet перезапустит контейнер
kubectl -n library get pods -w
```

## Тесты

```bat
cd services\catalog && python -m pytest -v      :: так же для readers и loans
```

## CI/CD (Jenkinsfile)

Checkout → Tools → Unit tests (3 сервиса) → Build images (4 образа) → Push to Docker Hub →
Deploy to Kubernetes → Smoke test (при ошибке — `kubectl rollout undo`) → Publish latest.
Развёртывание — только из `main`; `dev` — тесты, образы и Docker Hub; `feature/*` — только CI.
