# REST API

## 1. Общие положения

Префикс:

```text
/api/v1/
```

Формат: JSON. Даты: ISO 8601. Денежные значения передаются строками:

```json
{
  "amount": "310.00",
  "currency": "GEL"
}
```

Для расчётов используется Decimal.

### Ошибка

```json
{
  "error": {
    "code": "validation_error",
    "message": "Проверьте данные",
    "fields": {
      "amount": ["Сумма должна быть больше нуля"]
    }
  }
}
```

---

## 2. Авторизация

```text
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/token/refresh/
POST /api/v1/auth/logout/
GET  /api/v1/auth/me/
POST /api/v1/auth/password/reset/
POST /api/v1/auth/password/reset/confirm/
```

---

## 3. Профиль

```text
GET   /api/v1/profile/
PATCH /api/v1/profile/
POST   /api/v1/profile/signature/
DELETE /api/v1/profile/signature/
POST   /api/v1/profile/logo/
DELETE /api/v1/profile/logo/
```

Основные поля:

- business_name;
- entrepreneur_status;
- tin;
- legal_address;
- email;
- phone;
- tax_rate;
- accounting_start_date;
- timezone;
- language;
- invoice_prefix;
- next_invoice_number;
- telegram_connected.

---

## 4. Telegram

```text
POST   /api/v1/telegram/link/
DELETE /api/v1/telegram/link/
POST   /api/v1/telegram/mini-app/auth/
POST   /api/v1/telegram/webhook/
```

Mini App передаёт `init_data`. Backend проверяет подпись и срок действия.

---

## 5. Счета и кошельки

```text
GET    /api/v1/accounts/
POST   /api/v1/accounts/
GET    /api/v1/accounts/{id}/
PATCH  /api/v1/accounts/{id}/
DELETE /api/v1/accounts/{id}/
POST   /api/v1/accounts/{id}/set-default/
POST   /api/v1/accounts/{id}/archive/
```

Фильтры:

- type;
- currency;
- is_active;
- use_in_invoices.

---

## 6. Контрагенты

```text
GET    /api/v1/counterparties/
POST   /api/v1/counterparties/
GET    /api/v1/counterparties/{id}/
PATCH  /api/v1/counterparties/{id}/
DELETE /api/v1/counterparties/{id}/
```

Фильтры: type, country, search.

---

## 7. Валюты и курсы

```text
GET  /api/v1/currencies/
GET  /api/v1/exchange-rates/?currency=USD&date=2026-03-30
POST /api/v1/exchange-rates/convert/
POST /api/v1/exchange-rates/crypto-estimate/
```

Пример расчёта:

```json
{
  "amount": "500.00",
  "currency": "USD",
  "date": "2026-03-30",
  "mode": "automatic"
}
```

Ответ:

```json
{
  "data": {
    "original_amount": "500.00",
    "currency": "USD",
    "rate_value": "2.700000",
    "rate_unit": "1",
    "amount_gel": "1350.00",
    "source": "nbg",
    "rate_date": "2026-03-30"
  }
}
```

Для криптовалюты обязательны asset, amount, rate или amount_gel, source и valued_at.

---

## 8. Доходы

```text
GET    /api/v1/incomes/
POST   /api/v1/incomes/
GET    /api/v1/incomes/{id}/
PATCH  /api/v1/incomes/{id}/
DELETE /api/v1/incomes/{id}/
POST   /api/v1/incomes/{id}/restore/
POST   /api/v1/incomes/preview/
GET    /api/v1/incomes/export.csv
GET    /api/v1/incomes/export.xlsx
```

Основные поля:

- received_at;
- description;
- additional_info;
- counterparty;
- account;
- payment_method;
- original_amount;
- original_currency;
- exchange_rate;
- exchange_rate_unit;
- exchange_rate_source;
- exchange_rate_date;
- amount_gel;
- declaration_category;
- invoice;
- document_number;
- document_date;
- vat_amount;
- comment;
- attachment.

Фильтры:

- date_from;
- date_to;
- month;
- year;
- account;
- counterparty;
- currency;
- declaration_category;
- invoice;
- search;
- ordering.

---

## 9. Отчёты

```text
GET /api/v1/reports/dashboard/
GET /api/v1/reports/monthly/?year=2026&month=7
GET /api/v1/reports/yearly/?year=2026
GET /api/v1/reports/accounts/?year=2026
GET /api/v1/reports/currencies/?year=2026
GET /api/v1/reports/declaration-categories/?year=2026&month=7
```

---

## 10. Налоговые периоды

```text
GET  /api/v1/tax-periods/
GET  /api/v1/tax-periods/{id}/
POST /api/v1/tax-periods/generate/
POST /api/v1/tax-periods/{id}/recalculate/
POST /api/v1/tax-periods/{id}/preview-tax-rate/
POST /api/v1/tax-periods/{id}/mark-submitted/
POST /api/v1/tax-periods/{id}/unmark-submitted/
POST /api/v1/tax-periods/{id}/mark-paid/
POST /api/v1/tax-periods/{id}/unmark-paid/
GET  /api/v1/tax-periods/{id}/declaration-values/
```

Отметка подачи:

- submitted_at;
- comment;
- confirmation_file.

Отметка оплаты:

- paid_at;
- paid_amount;
- comment;
- confirmation_file.

Пример значений:

```json
{
  "data": {
    "field_15": "43500.00",
    "field_17": "6000.00",
    "field_18": "0.00",
    "field_19": "0.00",
    "field_20": "4800.00",
    "field_21": "1200.00",
    "field_26": "60.00",
    "tax_rate": "1.00"
  }
}
```

---

## 11. Инвойсы

```text
GET    /api/v1/invoices/
POST   /api/v1/invoices/
GET    /api/v1/invoices/{id}/
PATCH  /api/v1/invoices/{id}/
DELETE /api/v1/invoices/{id}/
POST   /api/v1/invoices/{id}/preview/
POST   /api/v1/invoices/{id}/generate-pdf/
GET    /api/v1/invoices/{id}/pdf/
POST   /api/v1/invoices/{id}/send-to-telegram/
POST   /api/v1/invoices/{id}/send-email/
POST   /api/v1/invoices/{id}/create-share-link/
DELETE /api/v1/invoices/{id}/share-link/
POST   /api/v1/invoices/{id}/mark-sent/
POST   /api/v1/invoices/{id}/mark-paid/
POST   /api/v1/invoices/{id}/mark-partially-paid/
POST   /api/v1/invoices/{id}/cancel/
POST   /api/v1/invoices/{id}/create-income/
POST   /api/v1/invoices/{id}/duplicate/
```

Позиции передаются вложенным массивом:

```json
{
  "items": [
    {
      "description": "Индивидуальные занятия по программированию",
      "quantity": "1.00",
      "unit": "service",
      "unit_price": "310.00"
    }
  ]
}
```

Для создания дохода из оплаты обязательны фактическая дата, сумма, валюта, счёт, курс и категория.

---

## 12. Уведомления

```text
GET  /api/v1/notifications/
GET  /api/v1/notifications/{id}/
POST /api/v1/notifications/{id}/mark-read/
POST /api/v1/notifications/mark-all-read/
GET   /api/v1/notification-settings/
PATCH /api/v1/notification-settings/
```

Настройки:

- internal_enabled;
- telegram_enabled;
- email_enabled;
- send_time;
- tax_reminders_enabled;
- invoice_reminders_enabled.

---

## 13. Файлы и аудит

```text
POST   /api/v1/files/
POST   /api/v1/files/{id}/download-link/
DELETE /api/v1/files/{id}/
GET    /api/v1/audit/
```

Временная ссылка имеет срок действия.

---

## 14. Служебные endpoints

```text
GET /api/v1/health/
GET /api/v1/schema/
GET /api/v1/docs/
```

---

## 15. Права доступа

- неавторизованный пользователь видит только auth и Telegram-auth;
- обычный пользователь работает только со своими объектами;
- все queryset ограничиваются текущим пользователем;
- идентификатор объекта не является проверкой прав;
- файлы доступны только владельцу или по временной ссылке.

---

## 16. Идемпотентность

Для создания дохода, генерации PDF и отметки оплаты рекомендуется заголовок:

```text
Idempotency-Key
```

Повтор с тем же ключом не создаёт второй объект.

---

## 17. HTTP-статусы

- 200 — успешно;
- 201 — создано;
- 202 — принято в фон;
- 204 — удалено;
- 400 — неверные данные;
- 401 — нет авторизации;
- 403 — нет прав;
- 404 — объект не найден;
- 409 — конфликт;
- 422 — нарушение бизнес-правила;
- 429 — слишком много запросов;
- 500 — внутренняя ошибка.

---

## 18. Документация

OpenAPI должна содержать:

- поля;
- примеры;
- ошибки;
- схему авторизации;
- фильтры;
- статусы;
- перечисления валют, категорий и состояний.
