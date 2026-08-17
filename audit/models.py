from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Запись журнала аудита"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Владелец данных',
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        null=True,
        blank=True,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Кто выполнил действие',
        on_delete=models.SET_NULL,
        related_name='performed_audit_logs',
        null=True,
        blank=True,
    )

    action = models.CharField(
        verbose_name='Действие',
        max_length=100,
    )

    object_type = models.CharField(
        verbose_name='Тип объекта',
        max_length=100,
    )

    object_id = models.PositiveBigIntegerField(
        verbose_name='ID объекта',
        null=True,
        blank=True,
    )

    old_values = models.JSONField(
        verbose_name='Старые значения',
        default=dict,
        blank=True,
    )

    new_values = models.JSONField(
        verbose_name='Новые значения',
        default=dict,
        blank=True,
    )

    request_id = models.CharField(
        verbose_name='ID запроса',
        max_length=100,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        verbose_name='IP-адрес',
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        verbose_name='User Agent',
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-created_at']

        indexes = [
            models.Index(
                fields=['user', 'created_at'],
            ),
            models.Index(
                fields=['object_type', 'object_id'],
            ),
            models.Index(
                fields=['request_id'],
            ),
        ]

    def __str__(self):
        return f'{self.action}: {self.object_type} #{self.object_id}'
