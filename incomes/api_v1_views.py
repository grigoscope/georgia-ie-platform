from datetime import datetime, time, timedelta

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import DateField

from config.business_time import (
    get_business_timezone,
    period_bounds,
    year_bounds,
)
from config.openapi_parameters import (
    INCOME_FILTER_PARAMETERS,
)
from config.pagination import (
    StandardPageNumberPagination,
)
from exchange_rates.models import Currency
from exchange_rates.services import (
    GELConversionService,
    NBGRateError,
)
from idempotency.decorators import (
    idempotent,
)
from incomes.api_v1_serializers import (
    IncomePreviewSerializer,
)
from incomes.models import IncomeEntry
from incomes.services import (
    IncomeCategoryService,
    IncomeService,
)
from incomes.views import IncomeEntryViewSet


@extend_schema_view(
    list=extend_schema(
        tags=['Incomes'],
        parameters=(INCOME_FILTER_PARAMETERS),
    )
)
class IncomeEntryV1ViewSet(IncomeEntryViewSet):
    """Stage 4 API журнала доходов."""

    queryset = IncomeEntry.objects.all()

    pagination_class = StandardPageNumberPagination

    @idempotent
    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        return super().create(
            request,
            *args,
            **kwargs,
        )

    def get_queryset(self):
        queryset = super().get_queryset()

        params = self.request.query_params

        date_from_value = params.get('date_from')
        date_to_value = params.get('date_to')

        year_value = params.get('year')
        month_value = params.get('month')

        account = params.get('account')
        counterparty = params.get('counterparty')
        currency = params.get('currency')
        category = params.get('declaration_category')
        invoice = params.get('invoice')

        search = params.get('search')

        ordering = params.get(
            'ordering',
            '-received_at',
        )

        date_from = None
        date_to = None

        if date_from_value:
            date_from = self._parse_date(
                date_from_value,
                'date_from',
            )

        if date_to_value:
            date_to = self._parse_date(
                date_to_value,
                'date_to',
            )

        if date_from and date_to and date_from > date_to:
            raise ValidationError({'date_to': ('date_to не может быть раньше date_from.')})

        business_tz = get_business_timezone()

        if date_from:
            start = datetime.combine(
                date_from,
                time.min,
                tzinfo=business_tz,
            )

            queryset = queryset.filter(received_at__gte=start)

        if date_to:
            end_date = date_to + timedelta(days=1)

            end = datetime.combine(
                end_date,
                time.min,
                tzinfo=business_tz,
            )

            queryset = queryset.filter(received_at__lt=end)

        if month_value is not None:
            if year_value is None:
                raise ValidationError({'year': ('При указании month необходимо указать year.')})

            year = self._parse_integer(
                year_value,
                'year',
            )

            month = self._parse_integer(
                month_value,
                'month',
            )

            if month < 1 or month > 12:
                raise ValidationError({'month': ('Месяц должен быть от 1 до 12.')})

            start, end = period_bounds(
                year=year,
                month=month,
            )

            queryset = queryset.filter(
                received_at__gte=start,
                received_at__lt=end,
            )

        elif year_value is not None:
            year = self._parse_integer(
                year_value,
                'year',
            )

            start, end = year_bounds(year=year)

            queryset = queryset.filter(
                received_at__gte=start,
                received_at__lt=end,
            )

        if account:
            queryset = queryset.filter(financial_account_id=account)

        if counterparty:
            queryset = queryset.filter(counterparty_id=counterparty)

        if currency:
            if currency.isdigit():
                queryset = queryset.filter(original_currency_id=(int(currency)))
            else:
                queryset = queryset.filter(original_currency__code__iexact=(currency))

        if category:
            valid_categories = {value for value, _ in IncomeEntry.DECLARATION_CATEGORIES}

            if category not in valid_categories:
                raise ValidationError(
                    {'declaration_category': ('Некорректная категория декларации.')}
                )

            queryset = queryset.filter(declaration_category=category)

        if invoice:
            queryset = queryset.filter(invoice_id=invoice)

        if search:
            queryset = queryset.filter(
                Q(description__icontains=search)
                | Q(additional_info__icontains=(search))
                | Q(document_number__icontains=(search))
                | Q(comment__icontains=search)
                | Q(counterparty__name__icontains=(search))
            )

        allowed_orderings = {
            'received_at',
            '-received_at',
            'amount_gel',
            '-amount_gel',
            'original_amount',
            '-original_amount',
            'created_at',
            '-created_at',
        }

        if ordering not in allowed_orderings:
            raise ValidationError({'ordering': ('Недопустимое поле сортировки.')})

        return queryset.order_by(ordering)

    @action(
        detail=True,
        methods=['post'],
        url_path='restore',
    )
    def restore(
        self,
        request,
        pk=None,
    ):
        income = get_object_or_404(
            IncomeEntry.objects.filter(
                user=request.user,
                is_deleted=True,
            ),
            pk=pk,
        )

        service = IncomeService()

        income = service.restore_income(
            income=income,
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

        serializer = self.get_serializer(income)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='preview',
    )
    def preview(
        self,
        request,
    ):
        serializer = IncomePreviewSerializer(
            data=request.data,
            context={
                'request': request,
            },
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        account = data['financial_account']

        currency = data['original_currency']

        suggested_category = IncomeCategoryService.suggest(account)

        selected_category = data.get('declaration_category') or suggested_category

        service = GELConversionService()

        try:
            with transaction.atomic():
                conversion = service.convert(
                    amount=(data['original_amount']),
                    currency_code=(currency.code),
                    user=request.user,
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
                    rate_date=(data['received_at'].astimezone(get_business_timezone()).date()),
                )

                transaction.set_rollback(True)

        except NBGRateError as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            )

        except (
            ValueError,
            Currency.DoesNotExist,
        ) as error:
            raise ValidationError(
                {
                    'detail': str(error),
                }
            ) from error

        return Response(
            {
                'data': {
                    'original_amount': str(conversion['original_amount']),
                    'currency': (conversion['currency_code']),
                    'rate_value': str(conversion['rate_value']),
                    'rate_unit': (conversion['rate_unit']),
                    'rate_date': (conversion['rate_date'].isoformat()),
                    'source': (conversion['source']),
                    'amount_gel': str(conversion['amount_gel']),
                    'is_manual': (conversion['is_manual']),
                    'warnings': (
                        conversion.get(
                            'warnings',
                            [],
                        )
                    ),
                    'suggested_category': (suggested_category),
                    'declaration_category': (selected_category),
                }
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _parse_date(
        value,
        field_name,
    ):
        try:
            return DateField().run_validation(value)

        except Exception as error:
            raise ValidationError(
                {field_name: ('Дата должна быть в формате YYYY-MM-DD.')}
            ) from error

    @staticmethod
    def _parse_integer(
        value,
        field_name,
    ):
        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValidationError({field_name: ('Значение должно быть целым числом.')}) from error
