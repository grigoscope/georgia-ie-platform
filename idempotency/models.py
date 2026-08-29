from django.conf import settings
from django.db import models


class IdempotencyRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='idempotency_records',
    )

    key = models.CharField(
        max_length=255,
    )

    scope = models.CharField(
        max_length=255,
    )

    request_hash = models.CharField(
        max_length=64,
    )

    response_status = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    response_body = models.JSONField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'user',
                    'scope',
                    'key',
                ],
                name=('unique_idempotency_key_per_scope'),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    'user',
                    'created_at',
                ]
            ),
            models.Index(
                fields=[
                    'scope',
                    'key',
                ]
            ),
        ]

    def __str__(self):
        return f'{self.user_id}: {self.scope}: {self.key}'
