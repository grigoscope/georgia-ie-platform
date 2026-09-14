# Georgia IE Platform

Платформа для индивидуальных предпринимателей в Грузии: учёт доходов, расчёт сумм в GEL, подготовка данных для ежемесячной декларации, инвойсы, уведомления и Telegram Mini App.

Проект разработан как дипломная работа по профессии «Python-разработчик».

## Возможности

- регистрация и JWT-авторизация;
- профиль индивидуального предпринимателя;
- финансовые счета, карты, платёжные системы и криптокошельки;
- журнал доходов;
- автоматическая и ручная конвертация поступлений в GEL;
- фиксация исторического курса для каждой операции;
- категории декларации 18, 19, 20 и 21;
- месячные и годовые отчёты;
- налоговые периоды и расчёт предварительного налога;
- статусы подачи декларации и оплаты налога;
- PDF-инвойсы;
- отправка инвойсов через Telegram;
- внутренние и Telegram-уведомления;
- Django Admin;
- аудит административных действий;
- фоновые задачи Celery и Celery Beat;
- экспорт журнала в XLSX;
- React frontend;
- Telegram Mini App;
- Docker Compose;
- OpenAPI / Swagger / ReDoc.

## Стек

Backend: Python 3.12, Django, Django REST Framework, PostgreSQL, Redis, Celery, Celery Beat, Simple JWT, drf-spectacular, ReportLab, openpyxl, Gunicorn.

Frontend: React, TypeScript, Vite, React Router, Playwright.

Infrastructure: Docker, Docker Compose, Nginx, PostgreSQL, Redis.

## Архитектура

Основные сервисы Docker Compose:

- `backend` — Django + DRF + Gunicorn;
- `frontend` — production-сборка React;
- `postgres` — PostgreSQL;
- `redis` — брокер Celery и result backend;
- `celery-worker` — выполнение фоновых задач;
- `celery-beat` — запуск задач по расписанию;
- `nginx` — единая точка входа для frontend, API, static и media.

Все клиенты используют один REST API и общую базу данных.

## Быстрый запуск через Docker

```bash
git clone https://github.com/grigoscope/georgia-ie-platform.git
cd georgia-ie-platform
cp .env.example .env
docker compose build
docker compose up -d
docker compose ps
```

Заполните `.env` перед запуском.

При старте backend автоматически применяет миграции, создаёт или обновляет справочник валют, собирает static и запускает Gunicorn.

Приложение:

```text
http://localhost:8080
```

Healthcheck:

```text
http://localhost:8080/health/
```

## Переменные окружения

Основные переменные перечислены в `.env.example`.

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=georgia_ie
POSTGRES_USER=georgia_ie
POSTGRES_PASSWORD=

TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=

MINI_APP_URL=http://localhost:8080/mini-app

TIME_ZONE=UTC
BUSINESS_TIME_ZONE=Asia/Tbilisi
```

Секреты и реальные токены не должны попадать в Git.

## Миграции

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py makemigrations --check
```

## Справочник валют

При старте Docker справочник создаётся автоматически.

```bash
docker compose exec backend python manage.py seed_currencies
```

## Создание администратора

```bash
docker compose exec backend python manage.py createsuperuser
```

Django Admin:

```text
http://localhost:8080/admin/
```

## API

Основной префикс:

```text
/api/v1/
```

Swagger:

```text
http://localhost:8080/api/v1/docs/
```

ReDoc:

```text
http://localhost:8080/api/v1/redoc/
```

OpenAPI schema:

```text
http://localhost:8080/api/v1/schema/
```

## Тесты

```bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py test
docker compose build frontend
```

E2E frontend:

```bash
cd frontend
npm install
npm run test:e2e
```

## Celery

```bash
docker compose logs -f celery-worker
docker compose logs -f celery-beat
```

Основные фоновые задачи:

- обновление официальных валютных курсов;
- создание и пересчёт налоговых периодов;
- налоговые напоминания;
- доставка Telegram-уведомлений;
- повтор временно неудачных отправок;
- генерация и отправка PDF-инвойсов;
- проверка просроченных инвойсов;
- очистка временных ссылок;
- генерация XLSX-экспортов;
- очистка устаревших экспортов.

Бизнес-временная зона:

```text
Asia/Tbilisi
```

## Логи

```bash
docker compose logs -f
docker compose logs -f backend
docker compose logs -f nginx
```

## Остановка

```bash
docker compose down
```

С удалением volumes:

```bash
docker compose down -v
```

`docker compose down -v` удаляет данные PostgreSQL и Redis.

## Backup и restore PostgreSQL

После добавления скриптов:

```bash
./scripts/backup_db.sh
```

Восстановление:

```bash
./scripts/restore_db.sh backups/georgia_ie_YYYY-MM-DD_HH-MM-SS.dump
```

Для production резервные копии следует хранить отдельно от сервера приложения и регулярно проверять восстановление.

## Обновление проекта

```bash
git pull
docker compose build
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose ps
```

## Структура проекта

```text
accounts/               пользователи, профиль, авторизация
audit/                  аудит действий
config/                 настройки Django, URL, Celery
exchange_rates/         валюты и курсы
finances/               счета и финансовые источники
incomes/                журнал доходов, отчёты и экспорт
invoices/               инвойсы и PDF
notifications/          уведомления и фоновые задачи
taxes/                  налоговые периоды и расчёты
telegram_integration/   Telegram Bot и Mini App интеграция
uploads/                пользовательские файлы
frontend/               React + TypeScript frontend
nginx/                  конфигурация reverse proxy
reference/              исходное ТЗ и проектная документация
```

## Проектная документация

Исходное техническое задание хранится в:

- `docs/production.md` — production deployment и эксплуатация;
- `docs/backup-policy.md` — политика резервного копирования и восстановления;
- `docs/personal-data.md` — обработка персональных данных;

```text
reference/project-specification.md
```

Дополнительные материалы:

- `reference/service.md` — предметная область и бизнес-правила;
- `reference/api.md` — REST API;
- `reference/screens.md` — экраны сайта, Mini App и бота;
- `reference/step-1.md` — старт проекта;
- `reference/step-2.md` — модели данных;
- `reference/step-3.md` — доходы, валюты, отчёты и инвойсы;
- `reference/step-4.md` — REST API;
- `reference/step-5.md` — frontend и Telegram Mini App;
- `reference/step-6-adv.md` — Django Admin;
- `reference/step-7-adv.md` — Celery, бот и уведомления;
- `reference/step-8-adv.md` — Docker, тестирование и развёртывание.

## Ограничение

Платформа помогает вести учёт и подготавливать данные, но не заменяет бухгалтера или налогового консультанта и не отправляет декларации автоматически в государственные системы Грузии.

Пользователь самостоятельно подтверждает категорию дохода, валютный курс, налоговую ставку, факт подачи декларации и факт оплаты налога.

## Статус

Проект находится в активной разработке в рамках дипломной работы.

Основная backend-функциональность, frontend, Telegram Mini App, Django Admin, Celery и Docker-инфраструктура реализованы. Текущий этап — финальная инфраструктура, CI и production-документация.
