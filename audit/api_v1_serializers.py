from rest_framework import serializers

from audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Запись журнала аудита."""

    actor_email = serializers.EmailField(
        source='actor.email',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AuditLog

        fields = [
            'id',
            'actor_email',
            'action',
            'object_type',
            'object_id',
            'old_values',
            'new_values',
            'request_id',
            'ip_address',
            'user_agent',
            'created_at',
        ]

        read_only_fields = fields
