from django.conf import settings
from django.db import models
from django.db.models import Q


class FinancialAccount(models.Model):
    """Финансовый счёт пользователя."""

    ACCOUNT_TYPES = [
        ('bank_account', 'Банковский счёт'),
        ('bank_card', 'Банковская карта'),
        ('cash', 'Наличные'),
        ('physical_pos', 'Физический POS-терминал'),
        ('payment_system', 'Платёжная система'),
        ('crypto_wallet', 'Криптокошелёк'),
        ('other', 'Другое'),
    ]

    DECLARATION_CATEGORIES = [
        ('cash_register_18', 'Доходы через кассовый аппарат'),
        ('physical_pos_19', 'Доходы через физический POS-терминал'),
        ('cashless_20', 'Поступления на расчётные счета и другие безналичные расчёты'),
        ('other_21', 'Прочие доходы, включая бартер и операции по договорам с криптовалютой'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_accounts',
    )

    name = models.CharField(
        verbose_name='Название счёта',
        max_length=100,
    )

    type = models.CharField(
        verbose_name='Тип счёта',
        max_length=30,
        choices=ACCOUNT_TYPES,
    )

    default_currency = models.ForeignKey(
        'exchange_rates.Currency',
        on_delete=models.PROTECT,
        related_name='financial_accounts',
        verbose_name='Валюта по умолчанию',
    )

    provider_name = models.CharField(
        verbose_name='Банк или провайдер',
        max_length=100,
        blank=True,
    )

    account_holder = models.CharField(
        verbose_name='Владелец счёта',
        max_length=255,
        blank=True,
    )

    iban = models.CharField(
        verbose_name='IBAN',
        max_length=50,
        blank=True,
    )

    swift_bic = models.CharField(
        verbose_name='SWIFT/BIC',
        max_length=20,
        blank=True,
    )

    account_identifier = models.CharField(
        verbose_name='Идентификатор счёта',
        max_length=255,
        blank=True,
    )

    crypto_asset = models.CharField(
        verbose_name='Криптовалюта',
        max_length=20,
        blank=True,
    )

    crypto_network = models.CharField(
        verbose_name='Сеть криптовалюты',
        max_length=50,
        blank=True,
    )

    wallet_address = models.CharField(
        verbose_name='Адрес криптокошелька',
        max_length=255,
        blank=True,
    )

    memo_tag = models.CharField(
        verbose_name='Memo/Tag',
        max_length=100,
        blank=True,
    )

    default_declaration_category = models.CharField(
        verbose_name='Категория декларации по умолчанию',
        max_length=50,
        choices=DECLARATION_CATEGORIES,
        blank=True,
    )

    payment_instructions = models.TextField(
        verbose_name='Инструкция для оплаты',
        blank=True,
    )

    is_default = models.BooleanField(
        verbose_name='Счёт по умолчанию',
        default=False,
    )

    use_in_invoices = models.BooleanField(
        verbose_name='Использовать в инвойсах',
        default=False,
    )

    is_active = models.BooleanField(
        verbose_name='Активный счёт',
        default=True,
    )

    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name='Дата изменения',
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(is_default=True),
                name='unique_default_financial_account_per_user'
            )
        ]

        indexes = [
            models.Index(
                fields=['user', 'is_active']
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.user.email})'


class Counterparty(models.Model):
    ''''''