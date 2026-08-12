from django.conf import settings
from django.db import models


class TelegramConnection(models.Model):
    """Модель связи пользователя платформы с Telegram."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_connection',
    )

    telegram_user_id = models.BigIntegerField(
        verbose_name='Telegram User ID',
        unique=True,
    )

    telegram_chat_id = models.BigIntegerField(
        verbose_name='Telegram Chat ID',
    )

    username = models.CharField(
        verbose_name='Username в Telegram',
        max_length=64,
        blank=True,
    )

    first_name = models.CharField(
        verbose_name='Имя в Telegram',
        max_length=255,
        blank=True,
    )

    last_name = models.CharField(
        verbose_name='Фамилия в Telegram',
        max_length=255,
        blank=True,
    )

    language_code = models.CharField(
        verbose_name='Язык Telegram',
        max_length=10,
        blank=True,
    )

    is_active = models.BooleanField(
        verbose_name='Активная связь',
        default=True,
    )

    linked_at = models.DateTimeField(
        verbose_name='Дата подключения',
        auto_now_add=True,
    )

    last_seen_at = models.DateTimeField(
        verbose_name='Последняя активность',
        null=True,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=['telegram_chat_id'],
            )
        ]

    def __str__(self):
        return f'{self.user.email} - Telegram {self.telegram_user_id}'
