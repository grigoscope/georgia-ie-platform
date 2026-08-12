from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Currency(models.Model):
    """Модель валюты."""

    CURRENCY_TYPE = [
        ('fiat', 'Фиатная'),
        ('crypto', 'Крипто'),
    ]

    code = models.CharField(
        verbose_name='Код валюты',
        max_length=10,
        unique=True,
    )

    name = models.CharField(
        verbose_name='Название валюты',
        max_length=50,
    )

    kind = models.CharField(
        verbose_name='Тип валюты',
        choices=CURRENCY_TYPE,
        default='fiat',
        max_length=10,
    )

    decimal_places = models.PositiveSmallIntegerField(
        verbose_name='Количество знаков после запятой',
        default=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10),
        ],
    )

    is_active = models.BooleanField(
        verbose_name='Активная валюта',
        default=True,
    )

    def __str__(self):
        return f'{self.code} - {self.name}'


class ExchangeRate(models.Model):
    """Курс валюты к GEL"""

    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='exchange_rates',
    )

    rate_date = models.DateField(verbose_name='Дата курса')

    rate_time = models.TimeField(
        verbose_name='Время курса',
        null=True,
        blank=True,
    )

    rate_value = models.DecimalField(
        verbose_name='Значение курса',
        max_digits=20,
        decimal_places=10,
        validators=[
            MinValueValidator(Decimal('0.0000000001')),
        ],
    )

    rate_unit = models.PositiveIntegerField(
        verbose_name='Количество единиц валюты',
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )

    source = models.CharField(
        verbose_name='Источник курса',
        max_length=100,
    )

    is_manual = models.BooleanField(
        verbose_name='Курс введён вручную',
        default=False,
    )

    raw_reference = models.TextField(
        verbose_name='Исходная ссылка или данные',
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_exchange_rates',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=['currency', 'rate_date'],
            ),
        ]

    def __str__(self):
        return f'{self.currency.code}: {self.rate_unit} = {self.rate_value} GEL ({self.rate_date})'
