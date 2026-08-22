from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from incomes.reports import IncomeReportService


class BaseReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    report_service_class = IncomeReportService

    def get_service(self):
        return self.report_service_class()


class DashboardReportAPIView(BaseReportAPIView):
    """Dashboard по доходам."""

    def get(self, request):
        report = self.get_service().dashboard(
            user=request.user,
        )

        return Response(report)


class MonthlyReportAPIView(BaseReportAPIView):
    """Месячный отчёт."""

    def get(self, request):
        try:
            year = int(request.query_params.get('year'))
            month = int(request.query_params.get('month'))
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Параметры year и month обязательны и должны быть числами.'},
                status=400,
            )

        try:
            report = self.get_service().monthly(
                user=request.user,
                year=year,
                month=month,
            )
        except ValueError as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=400,
            )

        return Response(report)


class YearlyReportAPIView(BaseReportAPIView):
    """Годовой отчёт."""

    def get(self, request):
        try:
            year = int(request.query_params.get('year'))
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Параметр year обязателен и должен быть числом.'},
                status=400,
            )

        report = self.get_service().yearly(
            user=request.user,
            year=year,
        )

        return Response(report)


class AccountsReportAPIView(BaseReportAPIView):
    """Отчёт по счетам."""

    def get(self, request):
        filters, error_response = self._parse_filters(request)

        if error_response:
            return error_response

        report = self.get_service().by_accounts(
            user=request.user,
            **filters,
        )

        return Response(report)

    @staticmethod
    def _parse_filters(request):
        return parse_optional_period_filters(request)


class CurrenciesReportAPIView(BaseReportAPIView):
    """Отчёт по валютам."""

    def get(self, request):
        filters, error_response = parse_optional_period_filters(request)

        if error_response:
            return error_response

        report = self.get_service().by_currencies(
            user=request.user,
            **filters,
        )

        return Response(report)


class CounterpartiesReportAPIView(BaseReportAPIView):
    """Отчёт по контрагентам."""

    def get(self, request):
        filters, error_response = parse_optional_period_filters(request)

        if error_response:
            return error_response

        report = self.get_service().by_counterparties(
            user=request.user,
            **filters,
        )

        return Response(report)


class CategoriesReportAPIView(BaseReportAPIView):
    """Отчёт по графам декларации."""

    def get(self, request):
        filters, error_response = parse_optional_period_filters(request)

        if error_response:
            return error_response

        report = self.get_service().by_categories(
            user=request.user,
            **filters,
        )

        return Response(report)


def parse_optional_period_filters(request):
    """
    Разобрать необязательные year/month.

    Возможные варианты:
    без параметров;
    только year;
    year + month.
    """

    year_value = request.query_params.get('year')
    month_value = request.query_params.get('month')

    if month_value and not year_value:
        return {}, Response(
            {'detail': 'При указании month необходимо также указать year.'},
            status=400,
        )

    try:
        year = int(year_value) if year_value else None

        month = int(month_value) if month_value else None
    except ValueError:
        return {}, Response(
            {'detail': 'year и month должны быть числами.'},
            status=400,
        )

    if month is not None:
        if month < 1 or month > 12:
            return {}, Response(
                {'detail': 'Месяц должен быть от 1 до 12.'},
                status=400,
            )

    return {
        'year': year,
        'month': month,
    }, None
