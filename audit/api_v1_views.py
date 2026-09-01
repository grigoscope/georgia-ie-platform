from django.db.models import Q
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics
from rest_framework.exceptions import (
    ValidationError,
)
from rest_framework.fields import DateField
from rest_framework.permissions import (
    IsAuthenticated,
)

from audit.api_v1_serializers import (
    AuditLogSerializer,
)
from audit.models import AuditLog
from config.openapi_parameters import (
    AUDIT_FILTER_PARAMETERS,
)
from config.pagination import (
    StandardPageNumberPagination,
)


@extend_schema_view(
    get=extend_schema(
        tags=['Audit'],
        parameters=(AUDIT_FILTER_PARAMETERS),
    )
)
class AuditLogListAPIView(generics.ListAPIView):
    """Журнал действий пользователя."""

    serializer_class = AuditLogSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        queryset = AuditLog.objects.filter(user=self.request.user).select_related('actor')

        params = self.request.query_params

        action = params.get('action')

        object_type = params.get('object_type')

        object_id = params.get('object_id')

        request_id = params.get('request_id')

        date_from = params.get('date_from')

        date_to = params.get('date_to')

        search = params.get('search')

        ordering = params.get(
            'ordering',
            '-created_at',
        )

        if action:
            queryset = queryset.filter(action=action)

        if object_type:
            queryset = queryset.filter(object_type=object_type)

        if object_id:
            try:
                object_id = int(object_id)

            except ValueError as error:
                raise ValidationError(
                    {'object_id': ('object_id должен быть целым числом.')}
                ) from error

            queryset = queryset.filter(object_id=object_id)

        if request_id:
            queryset = queryset.filter(request_id=request_id)

        if date_from:
            parsed_date = self._parse_date(
                date_from,
                'date_from',
            )

            queryset = queryset.filter(created_at__date__gte=(parsed_date))

        if date_to:
            parsed_date = self._parse_date(
                date_to,
                'date_to',
            )

            queryset = queryset.filter(created_at__date__lte=(parsed_date))

        if search:
            queryset = queryset.filter(
                Q(action__icontains=search)
                | Q(object_type__icontains=(search))
                | Q(request_id__icontains=(search))
            )

        allowed_orderings = {
            'created_at',
            '-created_at',
            'action',
            '-action',
        }

        if ordering not in allowed_orderings:
            raise ValidationError({'ordering': ('Недопустимое поле сортировки.')})

        return queryset.order_by(ordering)

    @staticmethod
    def _parse_date(
        value,
        field_name,
    ):
        field = DateField()

        try:
            return field.run_validation(value)

        except ValidationError as error:
            raise ValidationError(
                {field_name: ('Дата должна быть в формате YYYY-MM-DD.')}
            ) from error
