from datetime import date, datetime, time
from decimal import Decimal

from audit.models import AuditLog


class AuditService:
    """Сервис записи журнала аудита."""

    @classmethod
    def log(
        cls,
        *,
        user,
        actor,
        action,
        obj,
        old_values=None,
        new_values=None,
        request_id='',
        ip_address=None,
        user_agent='',
    ):
        return AuditLog.objects.create(
            user=user,
            actor=actor,
            action=action,
            object_type=obj.__class__.__name__,
            object_id=obj.pk,
            old_values=cls._serialize_dict(
                old_values or {}
            ),
            new_values=cls._serialize_dict(
                new_values or {}
            ),
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def _serialize_dict(cls, data):
        return {
            key: cls._serialize_value(value)
            for key, value in data.items()
        }

    @staticmethod
    def _serialize_value(value):
        if isinstance(value, Decimal):
            return str(value)

        if isinstance(value, (datetime, date, time)):
            return value.isoformat()

        if hasattr(value, 'pk'):
            return value.pk

        return value