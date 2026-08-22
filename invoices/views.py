from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from invoices.models import Invoice
from invoices.pdf import InvoicePDFService
from invoices.serializers import InvoiceSerializer
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
            )
            .order_by(
                '-issue_date',
                '-id',
            )
        )

    def perform_create(self, serializer):
        data = serializer.validated_data.copy()

        items = data.pop('items')

        financial_account = data.pop(
            'financial_account'
        )

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
            financial_account=financial_account,
            items=items,
            discount=discount,
            extra_charge=extra_charge,
            **data,
        )

        serializer.instance = invoice

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Редактирование инвойса пока не реализовано.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(
        self,
        request,
        *args,
        **kwargs,
    ):
        return Response(
            {'detail': 'Редактирование инвойса пока не реализовано.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Удаление инвойса пока не реализовано.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
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
                {'detail': 'PDF для этого инвойса ещё не создан.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        invoice.pdf_file.open('rb')

        return FileResponse(
            invoice.pdf_file,
            content_type='application/pdf',
            as_attachment=True,
            filename=(f'invoice-{invoice.number}.pdf'),
        )
