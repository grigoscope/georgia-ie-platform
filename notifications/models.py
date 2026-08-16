from django.conf import settings
from django.db import models


class NotificationSettings(models.Model):
    """Модель настроек уведомлений пользователя"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings',
    )

    internal_enabled = models.BooleanField(
        verbose_name='Внутренние уведомления',
        default=True,
    )

    telegram_enabled = models.BooleanField(
        verbose_name='Уведомления в Telegram',
        default=False,
    )

    email_enabled = models.BooleanField(
        verbose_name='Email-уведомления',
        default=False,
    )

    send_time = models.TimeField(
        verbose_name='Время отправки уведомления',
        blank=True,
        null=True,
    )

    tax_reminders_enabled = models.BooleanField(
        verbose_name='Напоминания о налогах',
        default=True,
    )

    invoice_reminders_enabled = models.BooleanField(
        verbose_name='Напоминания об инвойсах',
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

    def __str__(self):
        return f'Настройки уведомлений: {self.user.email}'


class Notification(models.Model):
    """Модель уведомлений"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )

    type = models.CharField(
        verbose_name='Тип уведомления',
        max_length=50,
    )

    title = models.CharField(
        verbose_name='Заголовок',
        max_length=255,
    )

    message = models.TextField(
        verbose_name='Сообщение',
    )

    related_object_type = models.CharField(
        verbose_name='Тип связанного объекта',
        max_length=100,
        blank=True,
    )

    related_object_id = models.PositiveBigIntegerField(
        verbose_name='ID связанного объекта',
        null=True,
        blank=True,
    )

    action_url = models.CharField(
        verbose_name='Ссылка действия',
        max_length=500,
        blank=True,
    )

    scheduled_for = models.DateTimeField(
        verbose_name='Запланировано на',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    read_at = models.DateTimeField(
        verbose_name='Дата прочтения',
        null=True,
        blank=True,
    )

    telegram_sent_at = models.DateTimeField(
        verbose_name='Дата отправки в Telegram',
        null=True,
        blank=True,
    )

    email_sent_at = models.DateTimeField(
        verbose_name='Дата отправки по Email',
        null=True,
        blank=True,
    )

    delivery_status = models.CharField(
        verbose_name='Статус доставки',
        max_length=30,
        default='pending',
    )

    deduplication_key = models.CharField(
        verbose_name='Ключ дедупликации',
        max_length=255,
        blank=True,
    )

    error_message = models.TextField(
        verbose_name='Ошибка доставки',
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=['user', 'scheduled_for'],
            ),
            models.Index(
                fields=['user', 'read_at'],
            ),
        ]

    def __str__(self):
        return f'{self.title} ({self.user.email})'
