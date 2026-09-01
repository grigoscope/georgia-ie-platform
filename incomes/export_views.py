import csv
from io import BytesIO

from django.http import HttpResponse
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)
from openpyxl import Workbook
from openpyxl.styles import Font
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from config.business_time import (
    period_bounds,
    to_business_datetime,
    year_bounds,
)
from incomes.models import IncomeEntry


class IncomeExportMixin:
    """Общая логика экспорта доходов."""

    def get_queryset(self, request):
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
            return None, self._error_response(('При указании month необходимо также указать year.'))

        try:
            year = int(year_value) if year_value else None

            month = int(month_value) if month_value else None

        except ValueError:
            return None, self._error_response(('year и month должны быть числами.'))

        if month is not None:
            if month < 1 or month > 12:
                return (
                    None,
                    self._error_response(('Месяц должен быть от 1 до 12.')),
                )

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

        return queryset, None

    @staticmethod
    def export_headers():
        return [
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

    @staticmethod
    def income_row(income):
        received_at = to_business_datetime(income.received_at)

        return [
            received_at.date(),
            income.description,
            (income.counterparty.name if income.counterparty else ''),
            income.financial_account.name,
            income.document_number,
            income.original_amount,
            income.original_currency.code,
            income.exchange_rate_value,
            income.exchange_rate_unit,
            income.exchange_rate_source,
            income.amount_gel,
            income.declaration_category,
            income.vat_amount,
            (income.invoice.number if income.invoice else ''),
            income.comment,
        ]

    @staticmethod
    def _error_response(message):
        return Response(
            {
                'detail': message,
            },
            status=400,
        )


class IncomeCSVExportAPIView(
    IncomeExportMixin,
    APIView,
):
    """Экспорт журнала доходов в CSV."""

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=['Incomes'],
        parameters=[
            OpenApiParameter(
                name='year',
                type=OpenApiTypes.INT,
                location=(OpenApiParameter.QUERY),
            ),
            OpenApiParameter(
                name='month',
                type=OpenApiTypes.INT,
                location=(OpenApiParameter.QUERY),
            ),
        ],
        responses={
            (
                200,
                'text/csv',
            ): OpenApiTypes.BINARY,
        },
    )
    def get(self, request):
        queryset, error = self.get_queryset(request)

        if error:
            return error

        response = HttpResponse(
            content_type=('text/csv; charset=utf-8'),
        )

        response['Content-Disposition'] = 'attachment; filename="incomes.csv"'

        response.write('\ufeff')

        writer = csv.writer(
            response,
            delimiter=';',
        )

        writer.writerow(self.export_headers())

        for income in queryset:
            row = self.income_row(income)

            row[0] = row[0].isoformat()

            writer.writerow(row)

        return response


class IncomeXLSXExportAPIView(
    IncomeExportMixin,
    APIView,
):
    """Экспорт журнала доходов в XLSX."""

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=['Incomes'],
        parameters=[
            OpenApiParameter(
                name='year',
                type=OpenApiTypes.INT,
                location=(OpenApiParameter.QUERY),
            ),
            OpenApiParameter(
                name='month',
                type=OpenApiTypes.INT,
                location=(OpenApiParameter.QUERY),
            ),
        ],
        responses={
            (
                200,
                ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ): OpenApiTypes.BINARY,
        },
    )
    def get(self, request):
        queryset, error = self.get_queryset(request)

        if error:
            return error

        workbook = Workbook()

        worksheet = workbook.active
        worksheet.title = 'Incomes'

        worksheet.freeze_panes = 'A2'

        headers = self.export_headers()

        worksheet.append(headers)

        for cell in worksheet[1]:
            cell.font = Font(bold=True)

        for income in queryset:
            worksheet.append(self.income_row(income))

        for cell in worksheet['A'][1:]:
            cell.number_format = 'yyyy-mm-dd'

        money_columns = [
            'F',
            'H',
            'K',
            'M',
        ]

        for column in money_columns:
            for cell in worksheet[column][1:]:
                cell.number_format = '#,##0.00########'

        column_widths = {
            'A': 14,
            'B': 35,
            'C': 28,
            'D': 24,
            'E': 18,
            'F': 20,
            'G': 12,
            'H': 20,
            'I': 18,
            'J': 22,
            'K': 18,
            'L': 24,
            'M': 16,
            'N': 18,
            'O': 35,
        }

        for (
            column,
            width,
        ) in column_widths.items():
            (worksheet.column_dimensions[column].width) = width

        output = BytesIO()

        workbook.save(output)

        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type=('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        )

        response['Content-Disposition'] = 'attachment; filename="incomes.xlsx"'

        return response
