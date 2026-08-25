from rest_framework import serializers

from finances.models import (
    Counterparty,
    FinancialAccount,
)


class FinancialAccountSerializer(serializers.ModelSerializer):
    """Финансовый счёт."""

    default_currency_code = serializers.CharField(
        source='default_currency.code',
        read_only=True,
    )

    class Meta:
        model = FinancialAccount

        fields = [
            'id',
            'name',
            'type',
            'default_currency',
            'default_currency_code',
            'provider_name',
            'account_holder',
            'iban',
            'swift_bic',
            'account_identifier',
            'crypto_asset',
            'crypto_network',
            'wallet_address',
            'memo_tag',
            'default_declaration_category',
            'payment_instructions',
            'is_default',
            'use_in_invoices',
            'is_active',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'is_default',
            'created_at',
            'updated_at',
        ]

    def validate_default_currency(
        self,
        currency,
    ):
        if not currency.is_active:
            raise serializers.ValidationError('Нельзя использовать неактивную валюту.')

        return currency


class CounterpartySerializer(serializers.ModelSerializer):
    """Контрагент."""

    class Meta:
        model = Counterparty

        fields = [
            'id',
            'name',
            'type',
            'country',
            'tax_id',
            'address',
            'email',
            'phone',
            'comment',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]
