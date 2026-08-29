import hashlib
import json

from django.core.serializers.json import (
    DjangoJSONEncoder,
)
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import (
    APIException,
    ValidationError,
)
from rest_framework.response import Response

from idempotency.models import (
    IdempotencyRecord,
)


class IdempotencyConflict(APIException):
    status_code = 409
    default_detail = 'Этот Idempotency-Key уже использован для другого запроса.'
    default_code = 'idempotency_conflict'


class IdempotencyService:
    @classmethod
    def execute(
        cls,
        *,
        user,
        key,
        scope,
        request_data,
        callback,
    ):
        if len(key) > 255:
            raise ValidationError(
                {'Idempotency-Key': ('Ключ не должен быть длиннее 255 символов.')}
            )

        request_hash = cls._request_hash(request_data)

        with transaction.atomic():
            record, _ = IdempotencyRecord.objects.get_or_create(
                user=user,
                scope=scope,
                key=key,
                defaults={
                    'request_hash': (request_hash),
                },
            )

            record = IdempotencyRecord.objects.select_for_update().get(pk=record.pk)

            if record.request_hash != request_hash:
                raise IdempotencyConflict()

            if record.completed_at is not None:
                response = Response(
                    record.response_body,
                    status=(record.response_status),
                )

                response['Idempotent-Replayed'] = 'true'

                return response

            response = callback()

            if response.status_code >= 500:
                record.delete()

                return response

            record.response_status = response.status_code

            record.response_body = cls._json_safe(response.data)

            record.completed_at = timezone.now()

            record.save(
                update_fields=[
                    'response_status',
                    'response_body',
                    'completed_at',
                    'updated_at',
                ]
            )

            response['Idempotent-Replayed'] = 'false'

            return response

    @classmethod
    def _request_hash(
        cls,
        request_data,
    ):
        payload = json.dumps(
            request_data,
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=False,
            cls=DjangoJSONEncoder,
        )

        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    @staticmethod
    def _json_safe(value):
        return json.loads(
            json.dumps(
                value,
                ensure_ascii=False,
                cls=DjangoJSONEncoder,
            )
        )
