# Production deployment

## Environment

В production используется отдельный `.env`, который не хранится в Git.

Обязательные настройки:

```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
```

Все секреты должны передаваться через переменные окружения.

## HTTPS

Production-развёртывание должно использовать HTTPS.

TLS может завершаться:

- на внешнем reverse proxy;
- на load balancer;
- на Nginx с установленным сертификатом.

Django настроен для определения HTTPS через заголовок `X-Forwarded-Proto`.

Telegram webhook должен использовать только HTTPS URL.

## Docker

Запуск:

```bash
docker compose build
docker compose up -d
```

Проверка:

```bash
docker compose ps
```

Healthcheck:

```text
/health/
```

## Миграции

```bash
docker compose exec backend python manage.py migrate
```

## Static и media

Static собираются автоматически при старте backend.

Media хранятся в Docker volume.

Для production рекомендуется использовать отдельное persistent storage или object storage.

## Upload limits

Максимальный размер файла задаётся через:

```env
MAX_UPLOAD_SIZE=
```

Рекомендуется также ограничивать размер запроса на уровне Nginx.

## Logs

Backend:

```bash
docker compose logs -f backend
```

Celery worker:

```bash
docker compose logs -f celery-worker
```

Celery Beat:

```bash
docker compose logs -f celery-beat
```

Nginx:

```bash
docker compose logs -f nginx
```

В production рекомендуется централизованное хранение логов и уведомление об ошибках.

## Monitoring

Необходимо контролировать:

- состояние Docker-сервисов;
- healthcheck backend;
- доступность PostgreSQL;
- доступность Redis;
- свободное место на диске;
- размер media;
- размер PostgreSQL;
- состояние Celery worker;
- состояние Celery Beat;
- ошибки Telegram API.

## Restart

Все основные сервисы Docker Compose используют политику автоматического перезапуска.

После обновления:

```bash
git pull
docker compose build
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose ps
```

## PDF retention

PDF-инвойсы являются пользовательскими данными.

В production необходимо определить период хранения файлов в соответствии с требованиями сервиса.

Удаление файлов не должно нарушать целостность записей об инвойсах и аудите.

## Before deployment

Перед production deployment необходимо проверить:

```bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check
docker compose exec backend python manage.py test
```

Также необходимо проверить frontend build и GitHub Actions CI.
