# Docker-образ сервиса web: веб-сервер nginx + веб-интерфейс библиотеки.
FROM nginx:1.27-alpine

# своя конфигурация вместо стандартной
COPY nginx.conf /etc/nginx/conf.d/default.conf
# статические файлы сайта
COPY static/ /usr/share/nginx/html/

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/nginx-health || exit 1
