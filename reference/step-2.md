# Этап 2. Проработка моделей данных

## Критерии достижения

1. Созданы основные модели и связи.
2. Добавлены ограничения базы.
3. Созданы миграции и индексы.
4. Все денежные поля используют DecimalField.
5. Данные пользователей изолированы.

## 1. User

Поля:

- email;
- password;
- first_name;
- last_name;
- is_active;
- is_staff;
- date_joined;
- last_login.

Email уникален и используется как логин.

## 2. EntrepreneurProfile

Связь один к одному с User.

Поля:

- business_name;
- entrepreneur_status;
- tin;
- legal_address;
- phone;
- public_email;
- tax_rate;
- accounting_start_date;
- timezone;
- language;
- invoice_prefix;
- next_invoice_number;
- signature_file;
- logo_file;
- created_at;
- updated_at.

## 3. TelegramConnection

Поля:

- user;
- telegram_user_id;
- telegram_chat_id;
- username;
- first_name;
- last_name;
- language_code;
- is_active;
- linked_at;
- last_seen_at.

Telegram user ID уникален.

## 4. FinancialAccount

Поля:

- user;
- name;
- type;
- default_currency;
- provider_name;
- account_holder;
- iban;
- swift_bic;
- account_identifier;
- crypto_asset;
- crypto_network;
- wallet_address;
- memo_tag;
- default_declaration_category;
- payment_instructions;
- is_default;
- use_in_invoices;
- is_active;
- timestamps.

Типы:

- bank_account;
- bank_card;
- cash;
- physical_pos;
- payment_system;
- crypto_wallet;
- other.

Приватные ключи и пароли не хранятся.

## 5. Counterparty

Поля:

- user;
- name;
- type;
- country;
- tax_id;
- address;
- email;
- phone;
- comment;
- timestamps.

Типы: individual, entrepreneur, company.

## 6. Currency

Поля:

- code;
- name;
- kind;
- decimal_places;
- is_active.

Типы: fiat, crypto. Код уникален.

## 7. ExchangeRate

Поля:

- currency;
- rate_date;
- rate_time;
- rate_value;
- rate_unit;
- source;
- is_manual;
- raw_reference;
- created_by;
- created_at.

## 8. IncomeEntry

Поля:

- user;
- received_at;
- description;
- additional_info;
- counterparty;
- financial_account;
- payment_method;
- document_number;
- document_date;
- invoice;
- original_amount;
- original_currency;
- exchange_rate_value;
- exchange_rate_unit;
- exchange_rate_source;
- exchange_rate_date;
- exchange_rate_time;
- amount_gel;
- declaration_category;
- vat_amount;
- comment;
- attachment;
- is_deleted;
- deleted_at;
- timestamps.

Категории:

- cash_register_18;
- physical_pos_19;
- cashless_20;
- other_21.

Ограничения:

- суммы и курс больше нуля;
- для GEL курс 1;
- связанные объекты принадлежат владельцу;
- индексы по пользователю, дате и категории.

## 9. Invoice

Поля:

- user;
- number;
- issue_date;
- service_period_start;
- service_period_end;
- due_date;
- currency;
- language;
- status;
- counterparty;
- seller_snapshot;
- buyer_snapshot;
- payment_details_snapshot;
- subtotal;
- discount_amount;
- extra_charge_amount;
- total_amount;
- tax_note;
- tax_reference_amount;
- payment_purpose;
- notes;
- pdf_file;
- pdf_checksum;
- generated_at;
- sent_at;
- paid_at;
- cancelled_at;
- timestamps.

Номер уникален в пределах пользователя.

## 10. InvoiceItem

Поля:

- invoice;
- position;
- description;
- quantity;
- unit;
- unit_price;
- line_total.

## 11. InvoicePayment

Нужна для частичных оплат.

Поля:

- invoice;
- income_entry;
- amount;
- currency;
- paid_at;
- created_at.

## 12. TaxPeriod

Поля:

- user;
- year;
- month;
- field_18;
- field_19;
- field_20;
- field_21;
- field_17;
- field_15;
- tax_rate;
- field_26;
- calculation_status;
- declaration_status;
- submitted_at;
- submission_comment;
- submission_confirmation;
- payment_status;
- paid_at;
- paid_amount;
- payment_comment;
- payment_confirmation;
- deadline;
- is_overdue;
- changed_after_submission;
- calculated_at;
- timestamps.

Уникальность: user + year + month.

## 13. Notification

Поля:

- user;
- type;
- title;
- message;
- related_object_type;
- related_object_id;
- action_url;
- scheduled_for;
- created_at;
- read_at;
- telegram_sent_at;
- email_sent_at;
- delivery_status;
- deduplication_key;
- error_message.

## 14. NotificationSettings

Поля:

- user;
- internal_enabled;
- telegram_enabled;
- email_enabled;
- send_time;
- tax_reminders_enabled;
- invoice_reminders_enabled;
- timestamps.

## 15. AuditLog

Поля:

- user;
- actor;
- action;
- object_type;
- object_id;
- old_values;
- new_values;
- request_id;
- ip_address;
- user_agent;
- created_at.

Записи только для чтения.

## Связи

- User 1:1 EntrepreneurProfile;
- User 1:1 NotificationSettings;
- User 1:1 TelegramConnection;
- User 1:N FinancialAccount;
- User 1:N Counterparty;
- User 1:N IncomeEntry;
- User 1:N Invoice;
- User 1:N TaxPeriod;
- Invoice 1:N InvoiceItem;
- Invoice M:N IncomeEntry через InvoicePayment;
- Currency 1:N ExchangeRate.

## Сервисный слой

Рекомендуемые сервисы:

- IncomeCalculationService;
- ExchangeRateService;
- TaxPeriodCalculationService;
- InvoiceCalculationService;
- InvoicePdfService;
- NotificationService;
- TelegramAuthService.

Один расчёт должен использоваться API, админкой и Celery.

## Проверка этапа

- миграции применяются;
- чужой счёт нельзя связать с доходом;
- два периода одного месяца создать нельзя;
- номер инвойса уникален;
- суммы используют DecimalField;
- подготовлены фабрики или фикстуры.
