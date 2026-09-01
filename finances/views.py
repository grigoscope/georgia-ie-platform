from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import (
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response

from config.openapi_parameters import (
    ACCOUNT_FILTER_PARAMETERS,
    COUNTERPARTY_FILTER_PARAMETERS,
)
from config.pagination import (
    StandardPageNumberPagination,
)
from finances.models import (
    Counterparty,
    FinancialAccount,
)
from finances.serializers import (
    CounterpartySerializer,
    FinancialAccountSerializer,
)
from finances.services import (
    FinancialAccountService,
)


@extend_schema_view(
    list=extend_schema(
        tags=['Accounts'],
        parameters=(ACCOUNT_FILTER_PARAMETERS),
    )
)
class FinancialAccountViewSet(viewsets.ModelViewSet):
    """CRUD счетов пользователя."""

    queryset = FinancialAccount.objects.all()

    serializer_class = FinancialAccountSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        queryset = (
            FinancialAccount.objects.filter(user=self.request.user)
            .select_related('default_currency')
            .order_by(
                '-is_default',
                'name',
            )
        )

        account_type = self.request.query_params.get('type')

        currency = self.request.query_params.get('currency')

        is_active = self.request.query_params.get('is_active')

        use_in_invoices = self.request.query_params.get('use_in_invoices')

        if account_type:
            queryset = queryset.filter(type=account_type)

        if currency:
            if currency.isdigit():
                queryset = queryset.filter(default_currency_id=(int(currency)))
            else:
                queryset = queryset.filter(default_currency__code__iexact=(currency))

        if is_active is not None:
            value = self._parse_boolean(is_active)

            if value is not None:
                queryset = queryset.filter(is_active=value)

        if use_in_invoices is not None:
            value = self._parse_boolean(use_in_invoices)

            if value is not None:
                queryset = queryset.filter(use_in_invoices=value)

        return queryset

    def perform_create(
        self,
        serializer,
    ):
        service = FinancialAccountService()

        account = service.create(
            user=self.request.user,
            **serializer.validated_data,
        )

        serializer.instance = account

    def perform_update(
        self,
        serializer,
    ):
        service = FinancialAccountService()

        account = service.update(
            account=self.get_object(),
            **serializer.validated_data,
        )

        serializer.instance = account

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        account = self.get_object()

        try:
            account.delete()

        except ProtectedError:
            return Response(
                {
                    'detail': (
                        'Счёт уже используется '
                        'в документах или доходах. '
                        'Архивируйте его вместо '
                        'удаления.'
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        url_path='set-default',
    )
    def set_default(
        self,
        request,
        pk=None,
    ):
        account = self.get_object()

        service = FinancialAccountService()

        try:
            account = service.set_default(account=account)

        except DjangoValidationError as error:
            return Response(
                {
                    'detail': error.messages,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(account).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='archive',
    )
    def archive(
        self,
        request,
        pk=None,
    ):
        account = self.get_object()

        service = FinancialAccountService()

        account = service.archive(account=account)

        return Response(
            self.get_serializer(account).data,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _parse_boolean(value):
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


@extend_schema_view(
    list=extend_schema(
        tags=['Counterparties'],
        parameters=(COUNTERPARTY_FILTER_PARAMETERS),
    )
)
class CounterpartyViewSet(viewsets.ModelViewSet):
    """CRUD контрагентов пользователя."""

    queryset = Counterparty.objects.all()

    serializer_class = CounterpartySerializer

    permission_classes = [
        IsAuthenticated,
    ]

    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        queryset = Counterparty.objects.filter(user=self.request.user)

        counterparty_type = self.request.query_params.get('type')

        country = self.request.query_params.get('country')

        search = self.request.query_params.get('search')

        ordering = self.request.query_params.get(
            'ordering',
            'name',
        )

        if counterparty_type:
            queryset = queryset.filter(type=counterparty_type)

        if country:
            queryset = queryset.filter(country__iexact=country)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(tax_id__icontains=search)
                | Q(phone__icontains=search)
            )

        allowed_orderings = {
            'name',
            '-name',
            'created_at',
            '-created_at',
            'updated_at',
            '-updated_at',
        }

        if ordering not in allowed_orderings:
            ordering = 'name'

        return queryset.order_by(ordering)

    def perform_create(
        self,
        serializer,
    ):
        serializer.save(user=self.request.user)

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        counterparty = self.get_object()

        try:
            counterparty.delete()

        except ProtectedError:
            return Response(
                {
                    'detail': (
                        'Контрагент используется в доходах или инвойсах и не может быть удалён.'
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
