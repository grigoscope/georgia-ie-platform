from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Invoice(models.Model):
    """Модель выставляемого счёта."""

    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('ka', 'ქართული'),
    ]

    INVOICE_STATUS = [
        ('created', 'Создан'),
        ('pending', 'Ожидает оплаты'),
        ('partially_paid', 'Частично оплачен'),
        ('paid', 'Оплачен'),
        ('cancelled', 'Отменён'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invoices',
    )

    number = models.CharField(
        verbose_name='Номер выставляемого счёта',
        max_length=100,
    )

    issue_date = models.DateField(
        verbose_name='Дата выставления',
    )

    service_period_start = models.DateField(
        verbose_name='Начало периода оказания услуги',
        null=True,
        blank=True,
    )

    service_period_end = models.DateField(
        verbose_name='Конец периода оказания услуги',
        null=True,
        blank=True,
    )

    due_date = models.DateField(
        verbose_name='Срок оплаты',
        null=True,
        blank=True,
    )

    currency = models.ForeignKey(
        'exchange_rates.Currency',
        verbose_name='Валюта',
        on_delete=models.PROTECT,
        related_name='invoices',
    )

    language = models.CharField(
        verbose_name='Язык',
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='ru',
    )

    status = models.CharField(
        verbose_name='Статус',
        max_length=30,
        choices=INVOICE_STATUS,
        default='created',
    )

    counterparty = models.ForeignKey(
        'finances.Counterparty',
        verbose_name='Контрагент',
        on_delete=models.PROTECT,
        related_name='invoices',
    )

    seller_snapshot = models.JSONField(
        verbose_name='Снимок данных продавца',
        default=dict,
    )

    buyer_snapshot = models.JSONField(
        verbose_name='Снимок данных покупателя',
        default=dict,
    )

    payment_details_snapshot = models.JSONField(
        verbose_name='Снимок платёжных реквизитов',
        default=dict,
    )

    subtotal = models.DecimalField(
        verbose_name='Сумма до скидок и наценок',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    discount_amount = models.DecimalField(
        verbose_name='Сумма скидки',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    extra_charge_amount = models.DecimalField(
        verbose_name='Дополнительная наценка',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    total_amount = models.DecimalField(
        verbose_name='Итоговая сумма',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    tax_note = models.TextField(
        verbose_name='Примечание о налоге',
        blank=True,
    )

    tax_reference_amount = models.DecimalField(
        verbose_name='Справочная налоговая сумма',
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    payment_purpose = models.CharField(
        verbose_name='Назначение платежа',
        max_length=255,
        blank=True,
    )

    notes = models.TextField(
        verbose_name='Примечания',
        blank=True,
    )

    pdf_file = models.FileField(
        verbose_name='PDF-инвойс',
        upload_to='invoices/',
        null=True,
        blank=True,
    )

    pdf_checksum = models.CharField(
        verbose_name='Контрольная сумма PDF',
        max_length=64,
        blank=True,
    )

    generated_at = models.DateTimeField(
        verbose_name='Дата генерации PDF',
        null=True,
        blank=True,
    )

    sent_at = models.DateTimeField(
        verbose_name='Дата отправки',
        null=True,
        blank=True,
    )

    paid_at = models.DateTimeField(
        verbose_name='Дата оплаты',
        null=True,
        blank=True,
    )

    cancelled_at = models.DateTimeField(
        verbose_name='Дата отмены',
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
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'number'],
                name='unique_invoice_number_per_user',
            ),
        ]

        indexes = [
            models.Index(
                fields=['user', 'status'],
            ),
            models.Index(
                fields=['user', 'issue_date'],
            ),
        ]

    def __str__(self):
        return f'Invoice {self.number} ({self.user.email})'


class InvoiceItem(models.Model):
    """Позиция в инвойсе"""

    invoice = models.ForeignKey(
        Invoice,
        verbose_name='Инвойс',
        on_delete=models.CASCADE,
        related_name='invoice_items',
    )

    position = models.PositiveIntegerField(
        verbose_name='Номер позиции',
    )

    description = models.CharField(
        verbose_name='Описание позиции',
        max_length=255,
    )

    quantity = models.DecimalField(
        verbose_name='Количество',
        max_digits=12,
        decimal_places=3,
        default=Decimal('1.000'),
        validators=[
            MinValueValidator(Decimal('0.001')),
        ],
    )

    unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=50,
        default='service',
    )

    unit_price = models.DecimalField(
        verbose_name='Стоимость за единицу',
        max_digits=18,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    line_total = models.DecimalField(
        verbose_name='Итоговая стоимость позиции',
        max_digits=18,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['invoice', 'position'],
                name='unique_invoice_item_position',
            )
        ]
        ordering = ['position']

    def __str__(self):
        return f'{self.invoice.number} - {self.position}. {self.description}'


class InvoicePayment(models.Model):
    """Оплата инвойса"""

    invoice = models.ForeignKey(
        Invoice,
        verbose_name='Инвойс',
        on_delete=models.CASCADE,
        related_name='payments',
    )

    income_entry = models.ForeignKey(
        'incomes.IncomeEntry',
        verbose_name='Поступление',
        on_delete=models.PROTECT,
        related_name='invoice_payments',
    )

    amount = models.DecimalField(
        verbose_name='Сумма оплаты',
        max_digits=18,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.01')),
        ],
    )

    currency = models.ForeignKey(
        'exchange_rates.Currency',
        verbose_name='Валюта оплаты',
        on_delete=models.PROTECT,
        related_name='invoice_payments',
    )

    paid_at = models.DateTimeField(
        verbose_name='Дата и время оплаты',
    )

    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'invoice',
                    'income_entry',
                ],
                name='unique_invoice_income_payment',
            ),
        ]

    def __str__(self):
        return f'{self.invoice.number} - {self.amount} {self.currency.code}'
