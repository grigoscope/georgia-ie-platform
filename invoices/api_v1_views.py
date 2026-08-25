from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from config.pagination import (
    StandardPageNumberPagination,
)
from finances.models import FinancialAccount
from invoices.models import Invoice
from invoices.payment_services import (
    InvoicePaymentService,
)
from invoices.serializers import (
    InvoicePaymentInputSerializer,
)
from invoices.services import InvoiceService
from invoices.views import InvoiceViewSet


class InvoiceV1ViewSet(InvoiceViewSet):
    """Stage 4 API инвойсов."""

    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        queryset = (
            Invoice.objects.filter(user=self.request.user)
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
        )

        params = self.request.query_params

        status_value = params.get('status')

        date_from = params.get('date_from')

        date_to = params.get('date_to')

        counterparty = params.get('counterparty')

        currency = params.get('currency')

        overdue = params.get('overdue')

        search = params.get('search')

        ordering = params.get(
            'ordering',
            '-issue_date',
        )

        if status_value:
            valid_statuses = {value for value, _ in Invoice.INVOICE_STATUS}

            if status_value not in valid_statuses:
                raise ValidationError({'status': ('Некорректный статус инвойса.')})

            queryset = queryset.filter(status=status_value)

        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)

        if counterparty:
            queryset = queryset.filter(counterparty_id=counterparty)

        if currency:
            if currency.isdigit():
                queryset = queryset.filter(currency_id=int(currency))
            else:
                queryset = queryset.filter(currency__code__iexact=(currency))

        if overdue is not None:
            parsed = self._parse_bool(overdue)

            if parsed is None:
                raise ValidationError({'overdue': ('Используйте true или false.')})

            today = timezone.localdate()

            overdue_filter = Q(due_date__lt=today) & ~Q(
                status__in=[
                    'paid',
                    'cancelled',
                ]
            )

            if parsed:
                queryset = queryset.filter(overdue_filter)

            else:
                queryset = queryset.exclude(overdue_filter)

        if search:
            queryset = queryset.filter(
                Q(number__icontains=search)
                | Q(counterparty__name__icontains=(search))
                | Q(payment_purpose__icontains=(search))
                | Q(notes__icontains=search)
            )

        allowed_orderings = {
            'issue_date',
            '-issue_date',
            'due_date',
            '-due_date',
            'total_amount',
            '-total_amount',
            'created_at',
            '-created_at',
            'number',
            '-number',
        }

        if ordering not in allowed_orderings:
            raise ValidationError({'ordering': ('Недопустимое поле сортировки.')})

        return queryset.order_by(
            ordering,
            '-id',
        )

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        invoice = self.get_object()

        if invoice.status != 'draft':
            return Response(
                {'detail': ('Удалить можно только черновик инвойса.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        if invoice.payments.exists():
            return Response(
                {'detail': ('Инвойс с оплатами удалить нельзя.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        if invoice.pdf_file:
            invoice.pdf_file.delete(save=False)

        invoice.delete()

        return Response(status=(status.HTTP_204_NO_CONTENT))

    @action(
        detail=True,
        methods=['post'],
        url_path='preview',
    )
    def preview(
        self,
        request,
        pk=None,
    ):
        """
        Получить готовые данные
        предпросмотра без изменений.
        """

        invoice = self.get_object()

        payment_service = InvoicePaymentService()

        summary = payment_service.get_summary(invoice=invoice)

        return Response(
            {
                'data': {
                    'invoice': (self.get_serializer(invoice).data),
                    'payment_summary': {
                        'total_amount': str(summary['total_amount']),
                        'paid_amount': str(summary['paid_amount']),
                        'remaining_amount': str(summary['remaining_amount']),
                        'is_paid': (summary['is_paid']),
                    },
                }
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='pdf',
    )
    def pdf(
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
        methods=['post'],
        url_path='mark-sent',
    )
    @transaction.atomic
    def mark_sent(
        self,
        request,
        pk=None,
    ):
        invoice = Invoice.objects.select_for_update().get(pk=self.get_object().pk)

        if invoice.status == 'cancelled':
            return Response(
                {'detail': ('Отменённый инвойс нельзя отметить отправленным.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        if invoice.status == 'paid':
            return Response(
                {'detail': ('Оплаченный инвойс уже завершён.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        invoice.status = 'pending'
        invoice.sent_at = timezone.now()

        invoice.save(
            update_fields=[
                'status',
                'sent_at',
                'updated_at',
            ]
        )

        return Response(
            self.get_serializer(invoice).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='mark-paid',
    )
    @transaction.atomic
    def mark_paid(
        self,
        request,
        pk=None,
    ):
        invoice = Invoice.objects.select_for_update().get(pk=self.get_object().pk)

        if invoice.status == 'cancelled':
            return Response(
                {'detail': ('Отменённый инвойс нельзя отметить оплаченным.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        invoice.status = 'paid'
        invoice.paid_at = timezone.now()

        invoice.save(
            update_fields=[
                'status',
                'paid_at',
                'updated_at',
            ]
        )

        return Response(
            self.get_serializer(invoice).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='mark-partially-paid',
    )
    @transaction.atomic
    def mark_partially_paid(
        self,
        request,
        pk=None,
    ):
        invoice = Invoice.objects.select_for_update().get(pk=self.get_object().pk)

        if invoice.status == 'cancelled':
            return Response(
                {'detail': ('Отменённый инвойс нельзя отметить частично оплаченным.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        invoice.status = 'partially_paid'

        invoice.paid_at = None

        invoice.save(
            update_fields=[
                'status',
                'paid_at',
                'updated_at',
            ]
        )

        return Response(
            self.get_serializer(invoice).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='cancel',
    )
    @transaction.atomic
    def cancel(
        self,
        request,
        pk=None,
    ):
        invoice = Invoice.objects.select_for_update().get(pk=self.get_object().pk)

        if invoice.status == 'paid':
            return Response(
                {'detail': ('Полностью оплаченный инвойс нельзя отменить.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        invoice.status = 'cancelled'

        invoice.cancelled_at = timezone.now()

        invoice.save(
            update_fields=[
                'status',
                'cancelled_at',
                'updated_at',
            ]
        )

        return Response(
            self.get_serializer(invoice).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='create-income',
    )
    def create_income(
        self,
        request,
        pk=None,
    ):
        """
        Создать фактический доход
        из оплаты инвойса.
        """

        invoice = self.get_object()

        serializer = InvoicePaymentInputSerializer(
            data=request.data,
            context={
                'request': request,
            },
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        service = InvoicePaymentService()

        try:
            result = service.create_income_from_invoice(
                invoice=invoice,
                received_at=(data['received_at']),
                financial_account=(data['financial_account']),
                amount=data['amount'],
                declaration_category=(data.get('declaration_category')),
                tax_period_deadline=(data.get('tax_period_deadline')),
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

        summary = result['summary']

        return Response(
            {
                'data': {
                    'invoice_id': (result['invoice'].id),
                    'invoice_status': (result['invoice'].status),
                    'income_id': (result['income'].id),
                    'payment_id': (result['payment'].id),
                    'payment_amount': str(result['payment'].amount),
                    'paid_amount': str(summary['paid_amount']),
                    'remaining_amount': str(summary['remaining_amount']),
                    'is_paid': (summary['is_paid']),
                }
            },
            status=(status.HTTP_201_CREATED),
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='duplicate',
    )
    def duplicate(
        self,
        request,
        pk=None,
    ):
        invoice = self.get_object()

        account_id = invoice.payment_details_snapshot.get('account_id')

        account = FinancialAccount.objects.filter(
            id=account_id,
            user=request.user,
            is_active=True,
        ).first()

        if account is None:
            return Response(
                {'detail': ('Исходный платёжный счёт недоступен. Выберите другой счёт.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        items = [
            {
                'description': (item.description),
                'quantity': (item.quantity),
                'unit': item.unit,
                'unit_price': (item.unit_price),
            }
            for item in invoice.invoice_items.all()
        ]

        service = InvoiceService()

        try:
            duplicate = service.create_invoice(
                user=request.user,
                issue_date=(timezone.localdate()),
                currency=invoice.currency,
                counterparty=(invoice.counterparty),
                financial_account=account,
                items=items,
                language=invoice.language,
                service_period_start=(invoice.service_period_start),
                service_period_end=(invoice.service_period_end),
                due_date=None,
                discount=(invoice.discount_amount),
                extra_charge=(invoice.extra_charge_amount),
                tax_note=(invoice.tax_note),
                tax_reference_amount=(invoice.tax_reference_amount),
                payment_purpose=(invoice.payment_purpose),
                notes=invoice.notes,
            )

        except DjangoValidationError as error:
            return Response(
                {
                    'detail': error.messages,
                },
                status=(status.HTTP_400_BAD_REQUEST),
            )

        return Response(
            self.get_serializer(duplicate).data,
            status=(status.HTTP_201_CREATED),
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
