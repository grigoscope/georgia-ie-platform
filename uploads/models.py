from django.conf import settings
from django.db import models


def user_file_path(
    instance,
    filename,
):
    return f'user_files/{instance.user_id}/{filename}'


class UserFile(models.Model):
    """Загруженный файл пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
    )

    file = models.FileField(
        upload_to=user_file_path,
    )

    original_name = models.CharField(
        max_length=255,
    )

    content_type = models.CharField(
        max_length=255,
        blank=True,
    )

    size = models.PositiveBigIntegerField()

    related_object_type = models.CharField(
        max_length=100,
        blank=True,
    )

    related_object_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            '-created_at',
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
                    'user',
                    'related_object_type',
                    'related_object_id',
                ]
            ),
        ]

    def __str__(self):
        return f'{self.user_id}: {self.original_name}'
