-- Создание отдельной базы данных для каждого микросервиса (используется docker compose;
-- в Kubernetes тот же скрипт лежит в ConfigMap postgres-init, файл 10-postgres.yaml)
CREATE DATABASE catalog;
CREATE DATABASE readers;
CREATE DATABASE loans;
