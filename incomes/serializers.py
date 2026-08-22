from rest_framework import serializers

from incomes.models import IncomeEntry


class IncomeEntrySerializer(serializers.ModelSerializer):
    """Сериализатор дохода."""

    manual_rate_value = serializers.DecimalField(
        max_digits=20,
        decimal_places=10,
        required=False,
        write_only=True,
    )

    manual_rate_unit = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        write_only=True,
    )

    manual_source = serializers.CharField(
        required=False,
        default='manual',
        write_only=True,
    )

    ready_amount_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        required=False,
        write_only=True,
    )

    tax_period_deadline = serializers.DateField(
        required=False,
        write_only=True,
    )

    class Meta:
        model = IncomeEntry

        fields = [
            'id',
            'received_at',
            'description',
            'additional_info',
            'counterparty',
            'financial_account',
            'payment_method',
            'document_number',
            'document_date',
            'invoice',
            'original_amount',
            'original_currency',
            'exchange_rate_value',
            'exchange_rate_unit',
            'exchange_rate_source',
            'exchange_rate_date',
            'exchange_rate_time',
            'amount_gel',
            'declaration_category',
            'vat_amount',
            'comment',
            'attachment',
            'created_at',
            'updated_at',
            'manual_rate_value',
            'manual_rate_unit',
            'manual_source',
            'ready_amount_gel',
            'tax_period_deadline',
        ]

        read_only_fields = [
            'id',
            'exchange_rate_value',
            'exchange_rate_unit',
            'exchange_rate_source',
            'exchange_rate_date',
            'exchange_rate_time',
            'amount_gel',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        financial_account = attrs.get('financial_account')

        original_currency = attrs.get('original_currency')

        request = self.context.get('request')

        if request and financial_account:
            if financial_account.user_id != request.user.id:
                raise serializers.ValidationError(
                    {'financial_account': 'Этот финансовый счёт принадлежит другому пользователю.'}
                )

        if (
            original_currency
            and original_currency.kind == 'crypto'
            and not attrs.get('manual_rate_value')
            and not attrs.get('ready_amount_gel')
        ):
            raise serializers.ValidationError(
                {
                    'original_currency': 'Для криптовалюты необходимо '
                    'указать ручной курс или '
                    'GEL-эквивалент.'
                }
            )

        return attrs
