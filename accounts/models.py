from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Стандартная модель пользователя."""

    username = None

    email = models.EmailField(verbose_name='Email-адрес', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class EntrepreneurProfile(models.Model):
    """Профиль Индивидуального предпринимателя."""

    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('ka', 'ქართული'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entrepreneur_profile',
    )

    business_name = models.CharField(
        verbose_name='Название бизнеса',
        max_length=255,
    )

    entrepreneur_status = models.CharField(
        verbose_name='Статус предпринимателя',
        max_length=100,
        blank=True,
    )

    tin = models.CharField(
        verbose_name='ИНН',
        max_length=50,
    )

    legal_address = models.CharField(
        verbose_name='Юридический адрес',
        max_length=255,
        blank=True,
    )

    phone = models.CharField(
        verbose_name='Телефон',
        max_length=30,
        blank=True,
    )

    public_email = models.EmailField(
        verbose_name='Публичный email',
        blank=True,
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

    accounting_start_date = models.DateField(
        verbose_name='Дата начала учёта',
        null=True,
        blank=True,
    )

    timezone = models.CharField(
        verbose_name='Часовой пояс',
        max_length=50,
        default='Asia/Tbilisi',
    )

    language = models.CharField(
        verbose_name='Язык',
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='ru',
    )

    invoice_prefix = models.CharField(
        verbose_name='Префикс инвойса',
        max_length=20,
        default='INV-',
    )

    next_invoice_number = models.PositiveIntegerField(
        verbose_name='Следующий номер инвойса',
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )

    signature_file = models.FileField(
        verbose_name='Подпись',
        upload_to='signatures/',
        null=True,
        blank=True,
    )

    logo_file = models.FileField(
        verbose_name='Логотип',
        upload_to='logos/',
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

    def __str__(self):
        return self.business_name
