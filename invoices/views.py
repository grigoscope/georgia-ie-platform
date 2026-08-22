from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from invoices.models import Invoice
from invoices.payment_services import (
    InvoicePaymentService,
)
from invoices.pdf import InvoicePDFService
from invoices.serializers import (
    InvoicePaymentInputSerializer,
    InvoiceSerializer,
)
from invoices.services import InvoiceService


class InvoiceViewSet(viewsets.ModelViewSet):
    """API инвойсов."""

    serializer_class = InvoiceSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return (
            Invoice.objects.filter(
                user=self.request.user,
            )
            .select_related(
                'counterparty',
                'currency',
            )
            .prefetch_related(
                'invoice_items',
                'payments',
                'payments__currency',
                'payments__income_entry',
            )
            .order_by(
                '-issue_date',
                '-id',
            )
        )

    def perform_create(self, serializer):
        data = serializer.validated_data.copy()

        items = data.pop('items')

        financial_account = data.pop('financial_account')

        discount = data.pop(
            'discount_amount',
            0,
        )

        extra_charge = data.pop(
            'extra_charge_amount',
            0,
        )

        service = InvoiceService()

        invoice = service.create_invoice(
            user=self.request.user,
            financial_account=(financial_account),
            items=items,
            discount=discount,
            extra_charge=extra_charge,
            **data,
        )

        serializer.instance = invoice

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):
        return Response(
            {'detail': ('Редактирование инвойса пока не реализовано.')},
            status=(status.HTTP_405_METHOD_NOT_ALLOWED),
        )

    def partial_update(
        self,
        request,
        *args,
        **kwargs,
    ):
        return Response(
            {'detail': ('Редактирование инвойса пока не реализовано.')},
            status=(status.HTTP_405_METHOD_NOT_ALLOWED),
        )

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        return Response(
            {'detail': ('Удаление инвойса пока не реализовано.')},
            status=(status.HTTP_405_METHOD_NOT_ALLOWED),
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='generate-pdf',
    )
    def generate_pdf(
        self,
        request,
        pk=None,
    ):
        invoice = self.get_object()

        service = InvoicePDFService()

        service.generate(invoice=invoice)

        invoice.refresh_from_db()

        serializer = self.get_serializer(invoice)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='download-pdf',
    )
    def download_pdf(
        self,
        request,
        pk=None,
    ):
        invoice = self.get_object()

        if not invoice.pdf_file:
            return Response(
                {'detail': ('PDF для этого инвойса ещё не создан.')},
                status=(status.HTTP_404_NOT_FOUND),
            )

        invoice.pdf_file.open('rb')

        return FileResponse(
            invoice.pdf_file,
            content_type='application/pdf',
            as_attachment=True,
            filename=(f'invoice-{invoice.number}.pdf'),
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='payment-summary',
    )
    def payment_summary(
        self,
        request,
        pk=None,
    ):
        """Получить состояние оплаты."""

        invoice = self.get_object()

        service = InvoicePaymentService()

        summary = service.get_summary(invoice=invoice)

        return Response(
            {
                'invoice_id': invoice.id,
                'number': invoice.number,
                'status': invoice.status,
                'currency': (invoice.currency.code),
                'total_amount': (summary['total_amount']),
                'paid_amount': (summary['paid_amount']),
                'remaining_amount': (summary['remaining_amount']),
                'is_paid': (summary['is_paid']),
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='create-payment',
    )
    def create_payment(
        self,
        request,
        pk=None,
    ):
        """Создать доход из оплаты инвойса."""

        invoice = self.get_object()

        input_serializer = InvoicePaymentInputSerializer(
            data=request.data,
            context={
                'request': request,
            },
        )

        input_serializer.is_valid(raise_exception=True)

        data = input_serializer.validated_data

        service = InvoicePaymentService()

        try:
            result = service.create_income_from_invoice(
                invoice=invoice,
                received_at=(data['received_at']),
                financial_account=(data['financial_account']),
                amount=data['amount'],
                declaration_category=(data.get('declaration_category')),
                tax_period_deadline=(data['tax_period_deadline']),
                payment_method=(
                    data.get(
                        'payment_method',
                        '',
                    )
                ),
                manual_rate_value=(data.get('manual_rate_value')),
                manual_rate_unit=(
                    data.get(
                        'manual_rate_unit',
                        1,
                    )
                ),
                manual_source=(
                    data.get(
                        'manual_source',
                        'manual',
                    )
                ),
                ready_amount_gel=(data.get('ready_amount_gel')),
                comment=(
                    data.get(
                        'comment',
                        '',
                    )
                ),
                actor=request.user,
                request_id=(
                    request.headers.get(
                        'X-Request-ID',
                        '',
                    )
                ),
                ip_address=(request.META.get('REMOTE_ADDR')),
                user_agent=(
                    request.headers.get(
                        'User-Agent',
                        '',
                    )
                ),
            )

        except DjangoValidationError as error:
            return Response(
                {
                    'detail': error.messages,
                },
                status=(status.HTTP_400_BAD_REQUEST),
            )

        invoice = result['invoice']
        income = result['income']
        payment = result['payment']
        summary = result['summary']

        return Response(
            {
                'invoice_id': invoice.id,
                'invoice_number': (invoice.number),
                'invoice_status': (invoice.status),
                'income_id': income.id,
                'payment_id': payment.id,
                'currency': (invoice.currency.code),
                'payment_amount': (payment.amount),
                'total_amount': (summary['total_amount']),
                'paid_amount': (summary['paid_amount']),
                'remaining_amount': (summary['remaining_amount']),
                'is_paid': (summary['is_paid']),
            },
            status=status.HTTP_201_CREATED,
        )
