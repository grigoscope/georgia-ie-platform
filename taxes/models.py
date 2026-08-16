from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class TaxPeriod(models.Model):
    """Налоговый период пользователя"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tax_periods',
    )

    year = models.PositiveSmallIntegerField(
        verbose_name='Год',
    )

    month = models.PositiveSmallIntegerField(
        verbose_name='Месяц',
    )

    field_18 = models.DecimalField(
        verbose_name='Доходы через кассовый аппарат',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    field_19 = models.DecimalField(
        verbose_name='Доходы через физический POS-терминал',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    field_20 = models.DecimalField(
        verbose_name='Поступления на расчётные счета и другие безналичные расчёты',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    field_21 = models.DecimalField(
        verbose_name='Прочие доходы, включая бартер и операции по договорам с криптовалютой',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    field_17 = models.DecimalField(
        verbose_name='Сумма дохода за предыдущий месяц',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    field_15 = models.DecimalField(
        verbose_name='Нарастающий итог с начала календарного (налогового) года',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    tax_rate = models.DecimalField(
        verbose_name='Налоговая ставка',
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    field_26 = models.DecimalField(
        verbose_name='Сумма налога',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    calculation_status = models.CharField(
        verbose_name='Статус расчёта',
        max_length=30,
        default='pending',
    )

    declaration_status = models.CharField(
        verbose_name='Статус декларации',
        max_length=30,
        default='not_submitted',
    )

    submitted_at = models.DateTimeField(
        verbose_name='Дата подачи декларации',
        null=True,
        blank=True,
    )

    submission_comment = models.TextField(
        verbose_name='Комментарий к подаче',
        blank=True,
    )

    submission_confirmation = models.FileField(
        verbose_name='Подтверждение подачи',
        upload_to='taxes/submissions/',
        null=True,
        blank=True,
    )

    payment_status = models.CharField(
        verbose_name='Статус оплаты',
        max_length=30,
        default='not_paid',
    )

    paid_at = models.DateTimeField(
        verbose_name='Дата оплаты',
        null=True,
        blank=True,
    )

    paid_amount = models.DecimalField(
        verbose_name='Оплаченная сумма',
        max_digits=18,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    payment_comment = models.TextField(
        verbose_name='Комментарий к оплате',
        blank=True,
    )

    payment_confirmation = models.FileField(
        verbose_name='Подтверждение оплаты',
        upload_to='taxes/payments/',
        null=True,
        blank=True,
    )

    deadline = models.DateField(
        verbose_name='Крайний срок',
    )

    is_overdue = models.BooleanField(
        verbose_name='Просрочено',
        default=False,
    )

    changed_after_submission = models.BooleanField(
        verbose_name='Изменено после подачи',
        default=False,
    )

    calculated_at = models.DateTimeField(
        verbose_name='Дата расчёта',
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
                fields=['user', 'year', 'month'],
                name='unique_tax_period_per_user',
            ),
            models.CheckConstraint(
                condition=Q(month__gte=1) & Q(month__lte=12),
                name='tax_period_valid_month',
            ),
        ]

        indexes = [
            models.Index(
                fields=['user', 'deadline'],
            ),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.year}/{self.month:02d}'
