from decimal import (
    ROUND_HALF_UP,
    Decimal,
)

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

from taxes.api_v1_serializers import (
    MarkPaidSerializer,
    MarkSubmittedSerializer,
    TaxPeriodGenerateSerializer,
    TaxPeriodSerializer,
    TaxRatePreviewSerializer,
)
from taxes.lifecycle_services import (
    TaxPeriodLifecycleService,
)
from taxes.models import TaxPeriod
from taxes.services import (
    TaxPeriodCalculationService,
)


class TaxPeriodViewSet(viewsets.ReadOnlyModelViewSet):
    """API налоговых периодов."""

    queryset = TaxPeriod.objects.all()

    serializer_class = TaxPeriodSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        queryset = TaxPeriod.objects.filter(user=self.request.user)

        params = self.request.query_params

        year = params.get('year')
        month = params.get('month')

        declaration_status = params.get('declaration_status')

        status_value = params.get('status')

        payment_status = params.get('payment_status')

        is_overdue = params.get('is_overdue')

        if year:
            try:
                year = int(year)
            except ValueError as error:
                raise ValidationError({'year': ('Год должен быть целым числом.')}) from error

            queryset = queryset.filter(year=year)

        if month:
            try:
                month = int(month)
            except ValueError as error:
                raise ValidationError({'month': ('Месяц должен быть целым числом.')}) from error

            if month < 1 or month > 12:
                raise ValidationError({'month': ('Месяц должен быть от 1 до 12.')})

            queryset = queryset.filter(month=month)

        if declaration_status:
            queryset = queryset.filter(declaration_status=(declaration_status))

        elif status_value:
            queryset = queryset.filter(declaration_status=(status_value))

        if payment_status:
            queryset = queryset.filter(payment_status=(payment_status))

        if is_overdue is not None:
            parsed = self._parse_bool(is_overdue)

            if parsed is None:
                raise ValidationError({'is_overdue': ('Используйте true или false.')})

            queryset = queryset.filter(is_overdue=parsed)

        return queryset.order_by(
            '-year',
            '-month',
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='generate',
    )
    def generate(
        self,
        request,
    ):
        serializer = TaxPeriodGenerateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        year = serializer.validated_data['year']

        month = serializer.validated_data['month']

        existed = TaxPeriod.objects.filter(
            user=request.user,
            year=year,
            month=month,
        ).exists()

        service = TaxPeriodCalculationService()

        period = service.recalculate_period(
            user=request.user,
            year=year,
            month=month,
        )

        result = self.get_serializer(period)

        return Response(
            result.data,
            status=(status.HTTP_200_OK if existed else status.HTTP_201_CREATED),
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='recalculate',
    )
    def recalculate(
        self,
        request,
        pk=None,
    ):
        period = self.get_object()

        service = TaxPeriodCalculationService()

        period = service.recalculate_from_month(
            user=request.user,
            year=period.year,
            month=period.month,
        )

        return Response(
            self.get_serializer(period).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='preview-tax-rate',
    )
    def preview_tax_rate(
        self,
        request,
        pk=None,
    ):
        period = self.get_object()

        serializer = TaxRatePreviewSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        rate = serializer.validated_data['tax_rate']

        field_26 = (period.field_17 * rate / Decimal('100')).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

        return Response(
            {
                'data': {
                    'period_id': period.id,
                    'field_17': (str(period.field_17)),
                    'current_tax_rate': (str(period.tax_rate)),
                    'preview_tax_rate': (str(rate)),
                    'field_26': (str(field_26)),
                }
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='mark-submitted',
    )
    def mark_submitted(
        self,
        request,
        pk=None,
    ):
        period = self.get_object()

        serializer = MarkSubmittedSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        service = TaxPeriodLifecycleService()

        period = service.mark_submitted(
            period=period,
            actor=request.user,
            submitted_at=data.get('submitted_at'),
            comment=data.get(
                'comment',
                '',
            ),
            confirmation_file=data.get('confirmation_file'),
        )

        return Response(
            self.get_serializer(period).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='unmark-submitted',
    )
    def unmark_submitted(
        self,
        request,
        pk=None,
    ):
        period = self.get_object()

        service = TaxPeriodLifecycleService()

        period = service.unmark_submitted(
            period=period,
            actor=request.user,
        )

        return Response(
            self.get_serializer(period).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='mark-paid',
    )
    def mark_paid(
        self,
        request,
        pk=None,
    ):
        period = self.get_object()

        serializer = MarkPaidSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        service = TaxPeriodLifecycleService()

        try:
            period = service.mark_paid(
                period=period,
                actor=request.user,
                paid_at=data.get('paid_at'),
                paid_amount=data['paid_amount'],
                comment=data.get(
                    'comment',
                    '',
                ),
                confirmation_file=(data.get('confirmation_file')),
            )

        except ValueError as error:
            raise ValidationError({'paid_amount': str(error)}) from error

        return Response(
            self.get_serializer(period).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='unmark-paid',
    )
    def unmark_paid(
        self,
        request,
        pk=None,
    ):
        period = self.get_object()

        service = TaxPeriodLifecycleService()

        period = service.unmark_paid(
            period=period,
            actor=request.user,
        )

        return Response(
            self.get_serializer(period).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='declaration-values',
    )
    def declaration_values(
        self,
        request,
        pk=None,
    ):
        period = self.get_object()

        return Response(
            {
                'data': {
                    'field_15': str(period.field_15),
                    'field_17': str(period.field_17),
                    'field_18': str(period.field_18),
                    'field_19': str(period.field_19),
                    'field_20': str(period.field_20),
                    'field_21': str(period.field_21),
                    'field_26': str(period.field_26),
                    'tax_rate': str(period.tax_rate),
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
