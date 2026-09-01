from rest_framework import serializers

from notifications.models import (
    Notification,
    NotificationSettings,
)


class NotificationSerializer(serializers.ModelSerializer):
    """Уведомление пользователя."""

    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification

        fields = [
            'id',
            'type',
            'title',
            'message',
            'related_object_type',
            'related_object_id',
            'action_url',
            'scheduled_for',
            'created_at',
            'read_at',
            'is_read',
            'telegram_sent_at',
            'email_sent_at',
            'delivery_status',
            'error_message',
        ]

        read_only_fields = fields

    @staticmethod
    def get_is_read(
        notification,
    ) -> bool:
        return notification.read_at is not None


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Настройки уведомлений."""

    class Meta:
        model = NotificationSettings

        fields = [
            'internal_enabled',
            'telegram_enabled',
            'email_enabled',
            'send_time',
            'tax_reminders_enabled',
            'invoice_reminders_enabled',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'created_at',
            'updated_at',
        ]
