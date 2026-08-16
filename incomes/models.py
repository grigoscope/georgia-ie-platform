from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class IncomeEntry(models.Model):
    """Модель записи о полученном доходе"""

    DECLARATION_CATEGORIES = [
        ('cash_register_18', 'Доходы через кассовый аппарат'),
        ('physical_pos_19', 'Доходы через физический POS-терминал'),
        ('cashless_20', 'Поступления на расчётные счета и другие безналичные расчёты'),
        ('other_21', 'Прочие доходы, включая бартер и операции по договорам с криптовалютой'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='income_entries',
    )

    received_at = models.DateTimeField(
        verbose_name='Дата и время получения дохода',
    )

    description = models.CharField(
        verbose_name='Описание',
        max_length=255,
    )

    additional_info = models.TextField(
        verbose_name='Дополнительная информация',
        blank=True,
    )

    counterparty = models.ForeignKey(
        'finances.Counterparty',
        verbose_name='Контрагент',
        on_delete=models.PROTECT,
        related_name='income_entries',
        null=True,
        blank=True,
    )

    financial_account = models.ForeignKey(
        'finances.FinancialAccount',
        verbose_name='Финансовый счёт',
        on_delete=models.PROTECT,
        related_name='income_entries',
    )

    payment_method = models.CharField(
        verbose_name='Способ оплаты',
        max_length=50,
        blank=True,
    )

    document_number = models.CharField(
        verbose_name='Номер документа',
        max_length=100,
        blank=True,
    )

    document_date = models.DateField(
        verbose_name='Дата документа',
        null=True,
        blank=True,
    )

    invoice = models.ForeignKey(
        'invoices.Invoice',
        verbose_name='Инвойс',
        on_delete=models.SET_NULL,
        related_name='income_entries',
        null=True,
        blank=True,
    )

    original_amount = models.DecimalField(
        verbose_name='Сумма в исходной валюте',
        max_digits=28,
        decimal_places=10,
        validators=[MinValueValidator(Decimal('0.0000000001'))],
    )

    original_currency = models.ForeignKey(
        'exchange_rates.Currency',
        verbose_name='Исходная валюта',
        on_delete=models.PROTECT,
        related_name='income_entries',
    )

    exchange_rate_value = models.DecimalField(
        verbose_name='Курс к GEL',
        max_digits=20,
        decimal_places=10,
        validators=[MinValueValidator(Decimal('0.0000000001'))],
    )

    exchange_rate_unit = models.PositiveIntegerField(
        verbose_name='Количество единиц валюты для курса',
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )

    exchange_rate_source = models.CharField(
        verbose_name='Источник курса',
        max_length=100,
    )

    exchange_rate_date = models.DateField(
        verbose_name='Дата курса',
    )

    exchange_rate_time = models.TimeField(
        verbose_name='Время курса',
        blank=True,
        null=True,
    )

    amount_gel = models.DecimalField(
        verbose_name='Сумма в GEL',
        max_digits=18,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.01')),
        ],
    )

    declaration_category = models.CharField(
        verbose_name='Категория декларации',
        choices=DECLARATION_CATEGORIES,
        max_length=50,
    )

    vat_amount = models.DecimalField(
        verbose_name='Сумма НДС',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,
    )

    attachment = models.FileField(
        verbose_name='Вложение',
        upload_to='income_attachments/',
        null=True,
        blank=True,
    )

    is_deleted = models.BooleanField(
        verbose_name='Удалено',
        default=False,
    )

    deleted_at = models.DateTimeField(
        verbose_name='Дата удаления',
        null=True,
        blank=True,
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
        indexes = [
            models.Index(
                fields=['user', 'received_at'],
            ),
            models.Index(
                fields=['user', 'declaration_category'],
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(original_amount__gt=0),
                name='income_original_amount_positive',
            ),
            models.CheckConstraint(
                condition=Q(exchange_rate_value__gt=0),
                name='income_exchange_rate_positive',
            ),
            models.CheckConstraint(
                condition=Q(amount_gel__gt=0),
                name='income_amount_gel_positive',
            ),
        ]

    def __str__(self):
        return f'{self.description} - {self.amount_gel} GEL'

    def clean(self):
        super().clean()

        if self.financial_account_id and self.financial_account.user_id != self.user_id:
            raise ValidationError(
                {'financial_account': 'Финансовый счёт принадлежит другому пользователю.'}
            )

        if self.counterparty_id and self.counterparty.user_id != self.user_id:
            raise ValidationError({'counterparty': 'Контрагент принадлежит другому пользователю.'})

        if self.invoice_id and self.invoice.user_id != self.user_id:
            raise ValidationError({'invoice': 'Инвойс принадлежит другому пользователю.'})

        if (
            self.original_currency_id
            and self.original_currency.code == 'GEL'
            and (self.exchange_rate_value != Decimal('1') or self.exchange_rate_unit != 1)
        ):
            raise ValidationError('Для GEL курс должен быть равен 1.')
