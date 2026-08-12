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
