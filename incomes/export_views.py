import csv

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from config.business_time import (
    period_bounds,
    to_business_datetime,
    year_bounds,
)
from incomes.models import IncomeEntry


class IncomeCSVExportAPIView(APIView):
    """Экспорт журнала доходов в CSV."""

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        queryset = (
            IncomeEntry.objects.filter(
                user=request.user,
                is_deleted=False,
            )
            .select_related(
                'counterparty',
                'financial_account',
                'original_currency',
                'invoice',
            )
            .order_by('received_at')
        )

        year_value = request.query_params.get('year')

        month_value = request.query_params.get('month')

        if month_value and not year_value:
            return self._error_response('При указании month необходимо также указать year.')

        try:
            year = int(year_value) if year_value else None

            month = int(month_value) if month_value else None

        except ValueError:
            return self._error_response('year и month должны быть числами.')

        if month is not None:
            if month < 1 or month > 12:
                return self._error_response('Месяц должен быть от 1 до 12.')

            start, end = period_bounds(
                year=year,
                month=month,
            )

            queryset = queryset.filter(
                received_at__gte=start,
                received_at__lt=end,
            )

        elif year is not None:
            start, end = year_bounds(year=year)

            queryset = queryset.filter(
                received_at__gte=start,
                received_at__lt=end,
            )

        response = HttpResponse(
            content_type=('text/csv; charset=utf-8'),
        )

        response['Content-Disposition'] = 'attachment; filename="incomes.csv"'

        response.write('\ufeff')

        writer = csv.writer(
            response,
            delimiter=';',
        )

        writer.writerow(
            [
                'date',
                'description',
                'counterparty',
                'account',
                'document',
                'original_amount',
                'currency',
                'exchange_rate',
                'exchange_rate_unit',
                'exchange_rate_source',
                'amount_gel',
                'declaration_category',
                'vat_amount',
                'invoice',
                'comment',
            ]
        )

        for income in queryset:
            received_at = to_business_datetime(income.received_at)

            writer.writerow(
                [
                    (received_at.date().isoformat()),
                    income.description,
                    (income.counterparty.name if income.counterparty else ''),
                    (income.financial_account.name),
                    income.document_number,
                    income.original_amount,
                    (income.original_currency.code),
                    (income.exchange_rate_value),
                    (income.exchange_rate_unit),
                    (income.exchange_rate_source),
                    income.amount_gel,
                    (income.declaration_category),
                    income.vat_amount,
                    (income.invoice.number if income.invoice else ''),
                    income.comment,
                ]
            )

        return response

    @staticmethod
    def _error_response(message):
        from rest_framework.response import (
            Response,
        )

        return Response(
            {
                'detail': message,
            },
            status=400,
        )
