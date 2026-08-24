from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth
from django.utils import timezone

from config.business_time import (
    get_business_timezone,
    period_bounds,
    year_bounds,
)
from incomes.models import IncomeEntry
from taxes.models import TaxPeriod


class IncomeReportService:
    """Отчёты по журналу доходов."""

    MONEY_QUANT = Decimal('0.01')

    CATEGORY_CODES = (
        'cash_register_18',
        'physical_pos_19',
        'cashless_20',
        'other_21',
    )

    def dashboard(self, *, user):
        """Основные показатели для dashboard."""

        today = timezone.localdate(
            timezone=get_business_timezone(),
        )

        monthly = self.monthly(
            user=user,
            year=today.year,
            month=today.month,
        )

        yearly = self.yearly(
            user=user,
            year=today.year,
        )

        recent_incomes = (
            self._base_queryset(user=user)
            .select_related(
                'counterparty',
                'financial_account',
                'original_currency',
            )
            .order_by('-received_at')[:5]
        )

        return {
            'current_month': monthly,
            'current_year': {
                'year': yearly['year'],
                'total_gel': yearly['total_gel'],
                'count': yearly['count'],
            },
            'recent_incomes': [
                {
                    'id': income.id,
                    'received_at': income.received_at,
                    'description': income.description,
                    'amount_gel': income.amount_gel,
                    'currency': (income.original_currency.code),
                    'original_amount': (income.original_amount),
                    'category': (income.declaration_category),
                }
                for income in recent_incomes
            ],
        }

    def monthly(
        self,
        *,
        user,
        year,
        month,
    ):
        """Месячный отчёт."""

        self._validate_month(month)

        queryset = self._filtered_queryset(
            user=user,
            year=year,
            month=month,
        )

        category_rows = queryset.values('declaration_category').annotate(
            total_gel=Sum('amount_gel'),
            count=Count('id'),
        )

        categories = {
            category: {
                'total_gel': Decimal('0.00'),
                'count': 0,
            }
            for category in self.CATEGORY_CODES
        }

        for row in category_rows:
            category = row['declaration_category']

            if category not in categories:
                continue

            categories[category] = {
                'total_gel': self._money(row['total_gel']),
                'count': row['count'],
            }

        total_gel = self._money(
            sum(
                (data['total_gel'] for data in categories.values()),
                Decimal('0.00'),
            )
        )

        total_count = sum(data['count'] for data in categories.values())

        period = TaxPeriod.objects.filter(
            user=user,
            year=year,
            month=month,
        ).first()

        tax_period_total = period.field_17 if period is not None else None

        return {
            'year': year,
            'month': month,
            'total_gel': total_gel,
            'count': total_count,
            'categories': categories,
            'tax_period': (
                {
                    'id': period.id,
                    'field_17': period.field_17,
                    'field_15': period.field_15,
                    'field_26': period.field_26,
                    'declaration_status': (period.declaration_status),
                    'changed_after_submission': (period.changed_after_submission),
                }
                if period is not None
                else None
            ),
            'matches_tax_period': (tax_period_total is None or total_gel == tax_period_total),
        }

    def yearly(
        self,
        *,
        user,
        year,
    ):
        """Годовой отчёт."""

        queryset = self._filtered_queryset(
            user=user,
            year=year,
        )

        month_rows = (
            queryset.annotate(
                report_month=ExtractMonth(
                    'received_at',
                    tzinfo=get_business_timezone(),
                )
            )
            .values('report_month')
            .annotate(
                total_gel=Sum('amount_gel'),
                count=Count('id'),
            )
            .order_by('report_month')
        )

        month_data = {
            month: {
                'month': month,
                'total_gel': Decimal('0.00'),
                'count': 0,
            }
            for month in range(1, 13)
        }

        for row in month_rows:
            month = row['report_month']

            month_data[month] = {
                'month': month,
                'total_gel': self._money(row['total_gel']),
                'count': row['count'],
            }

        category_rows = queryset.values('declaration_category').annotate(
            total_gel=Sum('amount_gel'),
            count=Count('id'),
        )

        categories = {
            category: {
                'total_gel': Decimal('0.00'),
                'count': 0,
            }
            for category in self.CATEGORY_CODES
        }

        for row in category_rows:
            category = row['declaration_category']

            if category not in categories:
                continue

            categories[category] = {
                'total_gel': self._money(row['total_gel']),
                'count': row['count'],
            }

        aggregate = queryset.aggregate(
            total_gel=Sum(
                'amount_gel',
                default=Decimal('0.00'),
            ),
            count=Count('id'),
        )

        return {
            'year': year,
            'total_gel': self._money(aggregate['total_gel']),
            'count': aggregate['count'],
            'months': list(month_data.values()),
            'categories': categories,
        }

    def by_accounts(
        self,
        *,
        user,
        year=None,
        month=None,
    ):
        """Отчёт с группировкой по счетам."""

        queryset = self._filtered_queryset(
            user=user,
            year=year,
            month=month,
        )

        rows = (
            queryset.values(
                'financial_account_id',
                'financial_account__name',
            )
            .annotate(
                total_gel=Sum('amount_gel'),
                count=Count('id'),
            )
            .order_by('-total_gel')
        )

        return [
            {
                'account_id': (row['financial_account_id']),
                'account_name': (row['financial_account__name']),
                'total_gel': self._money(row['total_gel']),
                'count': row['count'],
            }
            for row in rows
        ]

    def by_currencies(
        self,
        *,
        user,
        year=None,
        month=None,
    ):
        """Отчёт с группировкой по исходным валютам."""

        queryset = self._filtered_queryset(
            user=user,
            year=year,
            month=month,
        )

        rows = (
            queryset.values(
                'original_currency_id',
                'original_currency__code',
                'original_currency__name',
            )
            .annotate(
                original_amount=Sum('original_amount'),
                total_gel=Sum('amount_gel'),
                count=Count('id'),
            )
            .order_by('-total_gel')
        )

        return [
            {
                'currency_id': (row['original_currency_id']),
                'currency_code': (row['original_currency__code']),
                'currency_name': (row['original_currency__name']),
                'original_amount': (row['original_amount']),
                'total_gel': self._money(row['total_gel']),
                'count': row['count'],
            }
            for row in rows
        ]

    def by_counterparties(
        self,
        *,
        user,
        year=None,
        month=None,
    ):
        """Отчёт с группировкой по контрагентам."""

        queryset = self._filtered_queryset(
            user=user,
            year=year,
            month=month,
        )

        rows = (
            queryset.values(
                'counterparty_id',
                'counterparty__name',
            )
            .annotate(
                total_gel=Sum('amount_gel'),
                count=Count('id'),
            )
            .order_by('-total_gel')
        )

        return [
            {
                'counterparty_id': (row['counterparty_id']),
                'counterparty_name': (row['counterparty__name'] or 'Без контрагента'),
                'total_gel': self._money(row['total_gel']),
                'count': row['count'],
            }
            for row in rows
        ]

    def by_categories(
        self,
        *,
        user,
        year=None,
        month=None,
    ):
        """Отчёт с группировкой по графам 18–21."""

        queryset = self._filtered_queryset(
            user=user,
            year=year,
            month=month,
        )

        rows = (
            queryset.values('declaration_category')
            .annotate(
                total_gel=Sum('amount_gel'),
                count=Count('id'),
            )
            .order_by('declaration_category')
        )

        row_mapping = {row['declaration_category']: row for row in rows}

        result = []

        for category in self.CATEGORY_CODES:
            row = row_mapping.get(category)

            result.append(
                {
                    'category': category,
                    'total_gel': self._money(row['total_gel'] if row else Decimal('0.00')),
                    'count': (row['count'] if row else 0),
                }
            )

        return result

    def _filtered_queryset(
        self,
        *,
        user,
        year=None,
        month=None,
    ):
        """Получить доходы для отчёта."""

        queryset = self._base_queryset(user=user)

        if month is not None:
            self._validate_month(month)

            if year is None:
                raise ValueError('Для фильтрации по месяцу необходимо указать год.')

            start, end = period_bounds(
                year=year,
                month=month,
            )

            return queryset.filter(
                received_at__gte=start,
                received_at__lt=end,
            )

        if year is not None:
            start, end = year_bounds(year=year)

            return queryset.filter(
                received_at__gte=start,
                received_at__lt=end,
            )

        return queryset

    @staticmethod
    def _base_queryset(*, user):
        """Только активные доходы пользователя."""

        return IncomeEntry.objects.filter(
            user=user,
            is_deleted=False,
        )

    @staticmethod
    def _validate_month(month):
        if month < 1 or month > 12:
            raise ValueError('Месяц должен быть от 1 до 12.')

    @classmethod
    def _money(cls, value):
        if value is None:
            value = Decimal('0.00')

        return Decimal(value).quantize(
            cls.MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )
