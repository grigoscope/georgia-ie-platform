from rest_framework import serializers

CATEGORY_CHOICES = [
    'cash_register_18',
    'physical_pos_19',
    'cashless_20',
    'other_21',
]


class CategoryTotalsSerializer(serializers.Serializer):
    total_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    count = serializers.IntegerField()


class TaxPeriodReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    field_17 = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    field_15 = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    field_26 = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    declaration_status = serializers.CharField()

    changed_after_submission = serializers.BooleanField()


class MonthlyReportSerializer(serializers.Serializer):
    year = serializers.IntegerField()

    month = serializers.IntegerField()

    total_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    count = serializers.IntegerField()

    categories = serializers.DictField(child=CategoryTotalsSerializer())

    tax_period = TaxPeriodReportSerializer(allow_null=True)

    matches_tax_period = serializers.BooleanField()


class YearMonthReportSerializer(serializers.Serializer):
    month = serializers.IntegerField()

    total_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    count = serializers.IntegerField()


class YearlyReportSerializer(serializers.Serializer):
    year = serializers.IntegerField()

    total_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    count = serializers.IntegerField()

    months = YearMonthReportSerializer(many=True)

    categories = serializers.DictField(child=CategoryTotalsSerializer())


class CurrentYearReportSerializer(serializers.Serializer):
    year = serializers.IntegerField()

    total_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    count = serializers.IntegerField()


class RecentIncomeReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    received_at = serializers.DateTimeField()

    description = serializers.CharField()

    amount_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    currency = serializers.CharField()

    original_amount = serializers.DecimalField(
        max_digits=28,
        decimal_places=10,
    )

    category = serializers.ChoiceField(choices=CATEGORY_CHOICES)


class DashboardReportSerializer(serializers.Serializer):
    current_month = MonthlyReportSerializer()

    current_year = CurrentYearReportSerializer()

    recent_incomes = RecentIncomeReportSerializer(many=True)


class AccountReportRowSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()

    account_name = serializers.CharField()

    total_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    count = serializers.IntegerField()


class CurrencyReportRowSerializer(serializers.Serializer):
    currency_id = serializers.IntegerField()

    currency_code = serializers.CharField()

    currency_name = serializers.CharField()

    original_amount = serializers.DecimalField(
        max_digits=28,
        decimal_places=10,
    )

    total_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    count = serializers.IntegerField()


class CategoryReportRowSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=CATEGORY_CHOICES)

    total_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    count = serializers.IntegerField()
