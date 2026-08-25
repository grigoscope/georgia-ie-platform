from decimal import Decimal

from rest_framework import serializers

from exchange_rates.models import Currency, ExchangeRate


class CurrencySerializer(serializers.ModelSerializer):
    """Валюта."""

    class Meta:
        model = Currency

        fields = [
            'id',
            'code',
            'name',
            'kind',
            'decimal_places',
            'is_active',
        ]

        read_only_fields = fields


class ExchangeRateSerializer(serializers.ModelSerializer):
    """Курс валюты к GEL."""

    currency = serializers.CharField(
        source='currency.code',
        read_only=True,
    )

    class Meta:
        model = ExchangeRate

        fields = [
            'id',
            'currency',
            'rate_date',
            'rate_time',
            'rate_value',
            'rate_unit',
            'source',
            'is_manual',
            'created_at',
        ]

        read_only_fields = fields


class ConversionSerializer(serializers.Serializer):
    """Расчёт суммы в GEL."""

    MODE_AUTOMATIC = 'automatic'
    MODE_MANUAL = 'manual'
    MODE_READY_GEL = 'ready_gel'

    MODE_CHOICES = [
        MODE_AUTOMATIC,
        MODE_MANUAL,
        MODE_READY_GEL,
    ]

    amount = serializers.DecimalField(
        max_digits=28,
        decimal_places=10,
        min_value=Decimal('0.0000000001'),
    )

    currency = serializers.CharField(
        max_length=10,
    )

    date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    mode = serializers.ChoiceField(
        choices=MODE_CHOICES,
        default=MODE_AUTOMATIC,
    )

    rate_value = serializers.DecimalField(
        max_digits=20,
        decimal_places=10,
        min_value=Decimal('0.0000000001'),
        required=False,
        allow_null=True,
    )

    rate_unit = serializers.IntegerField(
        min_value=1,
        required=False,
        default=1,
    )

    source = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=False,
    )

    amount_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal('0.01'),
        required=False,
        allow_null=True,
    )

    def validate_currency(self, value):
        value = value.strip().upper()

        if not Currency.objects.filter(
            code=value,
            is_active=True,
        ).exists():
            raise serializers.ValidationError('Неизвестная или неактивная валюта.')

        return value

    def validate(self, attrs):
        mode = attrs['mode']

        if mode == self.MODE_MANUAL:
            if attrs.get('rate_value') is None:
                raise serializers.ValidationError(
                    {'rate_value': ('Для ручного режима необходимо указать курс.')}
                )

            if not attrs.get('source'):
                raise serializers.ValidationError(
                    {'source': ('Для ручного курса необходимо указать источник.')}
                )

        if mode == self.MODE_READY_GEL:
            if attrs.get('amount_gel') is None:
                raise serializers.ValidationError(
                    {'amount_gel': ('Необходимо указать GEL-эквивалент.')}
                )

        return attrs


class CryptoEstimateSerializer(serializers.Serializer):
    """Ручная оценка криптовалюты в GEL."""

    asset = serializers.CharField(
        max_length=20,
    )

    amount = serializers.DecimalField(
        max_digits=28,
        decimal_places=10,
        min_value=Decimal('0.0000000001'),
    )

    rate = serializers.DecimalField(
        max_digits=20,
        decimal_places=10,
        min_value=Decimal('0.0000000001'),
        required=False,
        allow_null=True,
    )

    rate_unit = serializers.IntegerField(
        min_value=1,
        default=1,
        required=False,
    )

    amount_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal('0.01'),
        required=False,
        allow_null=True,
    )

    source = serializers.CharField(
        max_length=100,
    )

    valued_at = serializers.DateTimeField()

    def validate_asset(self, value):
        value = value.strip().upper()

        currency = Currency.objects.filter(
            code=value,
            is_active=True,
        ).first()

        if currency is None:
            raise serializers.ValidationError('Криптовалюта не найдена.')

        if currency.kind != 'crypto':
            raise serializers.ValidationError('Указанная валюта не является криптовалютой.')

        return value

    def validate(self, attrs):
        if attrs.get('rate') is None and attrs.get('amount_gel') is None:
            raise serializers.ValidationError(
                ('Для криптовалюты необходимо указать rate или amount_gel.')
            )

        if attrs.get('rate') is not None and attrs.get('amount_gel') is not None:
            raise serializers.ValidationError(
                ('Укажите либо rate, либо amount_gel, но не оба значения.')
            )

        return attrs
