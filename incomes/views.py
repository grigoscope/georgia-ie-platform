from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from incomes.models import IncomeEntry
from incomes.serializers import IncomeEntrySerializer
from incomes.services import IncomeService


class IncomeEntryViewSet(viewsets.ModelViewSet):
    """CRUD журнала доходов."""

    serializer_class = IncomeEntrySerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return (
            IncomeEntry.objects.filter(
                user=self.request.user,
                is_deleted=False,
            )
            .select_related(
                'counterparty',
                'financial_account',
                'original_currency',
                'invoice',
            )
            .order_by('-received_at')
        )

    def perform_create(self, serializer):
        data = serializer.validated_data.copy()

        manual_rate_value = data.pop(
            'manual_rate_value',
            None,
        )

        manual_rate_unit = data.pop(
            'manual_rate_unit',
            1,
        )

        manual_source = data.pop(
            'manual_source',
            'manual',
        )

        ready_amount_gel = data.pop(
            'ready_amount_gel',
            None,
        )

        tax_period_deadline = data.pop(
            'tax_period_deadline',
            None,
        )

        service = IncomeService()

        income = service.create_income(
            user=self.request.user,
            actor=self.request.user,
            manual_rate_value=manual_rate_value,
            manual_rate_unit=manual_rate_unit,
            manual_source=manual_source,
            ready_amount_gel=ready_amount_gel,
            tax_period_deadline=tax_period_deadline,
            **data,
        )

        serializer.instance = income

    def perform_update(self, serializer):
        income = self.get_object()

        data = serializer.validated_data.copy()

        manual_rate_value = data.pop(
            'manual_rate_value',
            None,
        )

        manual_rate_unit = data.pop(
            'manual_rate_unit',
            1,
        )

        manual_source = data.pop(
            'manual_source',
            'manual',
        )

        ready_amount_gel = data.pop(
            'ready_amount_gel',
            None,
        )

        tax_period_deadline = data.pop(
            'tax_period_deadline',
            None,
        )

        service = IncomeService()

        updated_income = service.update_income(
            income=income,
            actor=self.request.user,
            manual_rate_value=manual_rate_value,
            manual_rate_unit=manual_rate_unit,
            manual_source=manual_source,
            ready_amount_gel=ready_amount_gel,
            tax_period_deadline=tax_period_deadline,
            **data,
        )

        serializer.instance = updated_income

    def destroy(self, request, *args, **kwargs):
        income = self.get_object()

        service = IncomeService()

        service.delete_income(
            income=income,
            actor=request.user,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
