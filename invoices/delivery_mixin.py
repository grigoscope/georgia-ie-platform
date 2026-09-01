from django.http import FileResponse
from django.urls import reverse
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from invoices.delivery_serializers import (
    InvoiceEmailSerializer,
    InvoiceShareSerializer,
)
from invoices.delivery_services import (
    InvoiceDeliveryError,
    InvoiceDeliveryService,
    InvoiceShareLinkService,
)
from invoices.models import (
    InvoiceShareLink,
)
from telegram_integration.models import (
    TelegramConnection,
)


class InvoiceDeliveryMixin:
    """Действия доставки инвойса."""

    @action(
        detail=True,
        methods=['post'],
        url_path='send-to-telegram',
    )
    def send_to_telegram(
        self,
        request,
        pk=None,
    ):
        invoice = self.get_object()

        connection = TelegramConnection.objects.filter(
            user=request.user,
            is_active=True,
        ).first()

        if connection is None:
            return Response(
                {'detail': ('Telegram не подключён.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        service = InvoiceDeliveryService()

        try:
            service.send_to_telegram(
                invoice=invoice,
                connection=connection,
            )

        except InvoiceDeliveryError as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=(status.HTTP_502_BAD_GATEWAY),
            )

        invoice.refresh_from_db()

        return Response(
            self.get_serializer(invoice).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='send-email',
    )
    def send_email(
        self,
        request,
        pk=None,
    ):
        invoice = self.get_object()

        serializer = InvoiceEmailSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        recipient = serializer.validated_data.get('recipient') or invoice.buyer_snapshot.get(
            'email'
        )

        if not recipient:
            return Response(
                {'recipient': [('Не указан email получателя.')]},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        try:
            InvoiceDeliveryService().send_email(
                invoice=invoice,
                recipient=recipient,
            )

        except InvoiceDeliveryError as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=(status.HTTP_502_BAD_GATEWAY),
            )

        invoice.refresh_from_db()

        return Response(
            self.get_serializer(invoice).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='create-share-link',
    )
    def create_share_link(
        self,
        request,
        pk=None,
    ):
        invoice = self.get_object()

        serializer = InvoiceShareSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        link = InvoiceShareLinkService().create(
            invoice=invoice,
            expires_in_hours=(serializer.validated_data['expires_in_hours']),
        )

        url = request.build_absolute_uri(
            reverse(
                'invoice-share-public',
                kwargs={
                    'token': link.token,
                },
            )
        )

        return Response(
            {
                'data': {
                    'url': url,
                    'expires_at': (link.expires_at),
                }
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['delete'],
        url_path='share-link',
    )
    def share_link(
        self,
        request,
        pk=None,
    ):
        invoice = self.get_object()

        (InvoiceShareLinkService().revoke(invoice=invoice))

        return Response(status=(status.HTTP_204_NO_CONTENT))


class InvoiceSharePublicAPIView(APIView):
    """Публичное скачивание по token."""

    permission_classes = [
        AllowAny,
    ]

    authentication_classes = []

    @extend_schema(
        tags=['Invoices'],
        auth=[],
        responses={
            (
                200,
                'application/pdf',
            ): OpenApiTypes.BINARY,
        },
    )
    def get(
        self,
        request,
        token,
    ):
        link = (
            InvoiceShareLink.objects.select_related('invoice')
            .filter(
                token=token,
                revoked_at__isnull=True,
                expires_at__gt=(timezone.now()),
            )
            .first()
        )

        if link is None:
            return Response(
                {'detail': ('Ссылка недействительна или истекла.')},
                status=(status.HTTP_404_NOT_FOUND),
            )

        invoice = link.invoice

        if not invoice.pdf_file:
            return Response(
                {'detail': ('PDF недоступен.')},
                status=(status.HTTP_404_NOT_FOUND),
            )

        invoice.pdf_file.open('rb')

        return FileResponse(
            invoice.pdf_file,
            content_type='application/pdf',
            as_attachment=True,
            filename=(f'invoice-{invoice.number}.pdf'),
        )
