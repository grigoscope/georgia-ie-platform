# Этап 1. Создание и настройка проекта

## Критерии достижения

1. Создан новый Git-репозиторий.
2. Django-проект создан с нуля и запускается без ошибок.
3. Подключены PostgreSQL и Django REST Framework.
4. Настроены переменные окружения.
5. Создана базовая OpenAPI-схема.
6. Создана заготовка frontend-приложения без бизнес-логики.
7. Секреты не попадают в Git.

## Необходимые инструменты

- Git и GitHub;
- Python 3.12 или совместимая версия;
- PostgreSQL;
- Redis;
- Node.js;
- IDE;
- Telegram BotFather;
- Postman, Insomnia или Swagger UI.

## Порядок выполнения

1. Создать пустой репозиторий.
2. Добавить `.gitignore`.
3. Создать виртуальное окружение.
4. Установить Django и DRF.
5. Создать Django-проект.
6. Настроить конфигурацию через переменные окружения.
7. Подключить PostgreSQL.
8. Создать приложения предметной области:
   - accounts;
   - finances;
   - incomes;
   - exchange_rates;
   - invoices;
   - taxes;
   - notifications;
   - telegram_integration;
   - audit.
9. Настроить media и static.
10. Создать `/api/v1/health/`.
11. Настроить линтер и форматирование.
12. Создать frontend-приложение.
13. Добавить `.env.example`.
14. Описать запуск в README.
15. Сделать первый осмысленный commit.

Названия приложений можно изменить, если зоны ответственности останутся понятными.

## Минимальные переменные окружения

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DATABASE_URL
REDIS_URL
TELEGRAM_BOT_TOKEN
TELEGRAM_WEBHOOK_SECRET
MINI_APP_URL
EMAIL_URL
DEFAULT_FROM_EMAIL
TIME_ZONE
```

## Проверка этапа

- backend запускается;
- PostgreSQL доступен;
- миграции применяются;
- health endpoint отвечает;
- Swagger открывается;
- frontend запускается;
- `.env` игнорируется;
- README содержит команды запуска.
