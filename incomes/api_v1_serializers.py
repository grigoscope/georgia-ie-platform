from decimal import Decimal

from rest_framework import serializers

from exchange_rates.models import Currency
from finances.models import FinancialAccount
from incomes.models import IncomeEntry


class IncomePreviewSerializer(serializers.Serializer):
    """Предварительный расчёт дохода."""

    received_at = serializers.DateTimeField()

    financial_account = serializers.PrimaryKeyRelatedField(
        queryset=FinancialAccount.objects.all(),
    )

    original_amount = serializers.DecimalField(
        max_digits=28,
        decimal_places=10,
        min_value=Decimal('0.0000000001'),
    )

    original_currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.filter(
            is_active=True,
        ),
    )

    declaration_category = serializers.ChoiceField(
        choices=(IncomeEntry.DECLARATION_CATEGORIES),
        required=False,
        allow_null=True,
    )

    manual_rate_value = serializers.DecimalField(
        max_digits=20,
        decimal_places=10,
        min_value=Decimal('0.0000000001'),
        required=False,
        allow_null=True,
    )

    manual_rate_unit = serializers.IntegerField(
        min_value=1,
        required=False,
        default=1,
    )

    manual_source = serializers.CharField(
        max_length=100,
        required=False,
        default='manual',
    )

    ready_amount_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal('0.01'),
        required=False,
        allow_null=True,
    )

    def validate_financial_account(
        self,
        account,
    ):
        request = self.context.get('request')

        if request and account.user_id != request.user.id:
            raise serializers.ValidationError('Финансовый счёт принадлежит другому пользователю.')

        return account
