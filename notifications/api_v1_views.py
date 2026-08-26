from django.db.models import Q
from django.utils import timezone
from rest_framework import (
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.exceptions import (
    ValidationError,
)
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from config.pagination import (
    StandardPageNumberPagination,
)
from notifications.api_v1_serializers import (
    NotificationSerializer,
    NotificationSettingsSerializer,
)
from notifications.models import (
    Notification,
    NotificationSettings,
)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Уведомления текущего пользователя."""

    serializer_class = NotificationSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)

        params = self.request.query_params

        notification_type = params.get('type')

        is_read = params.get('is_read')

        delivery_status = params.get('delivery_status')

        search = params.get('search')

        ordering = params.get(
            'ordering',
            '-created_at',
        )

        if notification_type:
            queryset = queryset.filter(type=notification_type)

        if delivery_status:
            queryset = queryset.filter(delivery_status=(delivery_status))

        if is_read is not None:
            parsed = self._parse_bool(is_read)

            if parsed is None:
                raise ValidationError({'is_read': ('Используйте true или false.')})

            if parsed:
                queryset = queryset.filter(read_at__isnull=False)
            else:
                queryset = queryset.filter(read_at__isnull=True)

        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(message__icontains=search))

        allowed_orderings = {
            'created_at',
            '-created_at',
            'scheduled_for',
            '-scheduled_for',
        }

        if ordering not in allowed_orderings:
            raise ValidationError({'ordering': ('Недопустимое поле сортировки.')})

        return queryset.order_by(ordering)

    @action(
        detail=True,
        methods=['post'],
        url_path='mark-read',
    )
    def mark_read(
        self,
        request,
        pk=None,
    ):
        notification = self.get_object()

        if notification.read_at is None:
            notification.read_at = timezone.now()

            notification.save(
                update_fields=[
                    'read_at',
                ]
            )

        return Response(
            self.get_serializer(notification).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='mark-all-read',
    )
    def mark_all_read(
        self,
        request,
    ):
        now = timezone.now()

        updated = Notification.objects.filter(
            user=request.user,
            read_at__isnull=True,
        ).update(read_at=now)

        return Response(
            {
                'data': {
                    'updated': updated,
                }
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _parse_bool(value):
        value = str(value).lower()

        if value in {
            'true',
            '1',
            'yes',
        }:
            return True

        if value in {
            'false',
            '0',
            'no',
        }:
            return False

        return None


class NotificationSettingsAPIView(APIView):
    """Настройки уведомлений."""

    permission_classes = [
        IsAuthenticated,
    ]

    @staticmethod
    def _get_settings(user):
        settings_object, _ = NotificationSettings.objects.get_or_create(user=user)

        return settings_object

    def get(self, request):
        settings_object = self._get_settings(request.user)

        serializer = NotificationSettingsSerializer(settings_object)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        settings_object = self._get_settings(request.user)

        serializer = NotificationSettingsSerializer(
            settings_object,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
