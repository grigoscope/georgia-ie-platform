from rest_framework import serializers

from exchange_rates.models import Currency
from finances.models import Counterparty, FinancialAccount
from invoices.models import Invoice, InvoiceItem, InvoicePayment


class InvoiceItemInputSerializer(serializers.Serializer):
    """Позиция при создании инвойса."""

    description = serializers.CharField(
        max_length=255,
    )

    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        default='1.000',
    )

    unit = serializers.CharField(
        max_length=50,
        default='service',
    )

    unit_price = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
    )


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Позиция готового инвойса."""

    class Meta:
        model = InvoiceItem

        fields = [
            'id',
            'position',
            'description',
            'quantity',
            'unit',
            'unit_price',
            'line_total',
        ]


class InvoicePaymentSerializer(serializers.ModelSerializer):
    """Сохранённая оплата инвойса."""

    currency_code = serializers.CharField(
        source='currency.code',
        read_only=True,
    )

    income_entry_id = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = InvoicePayment

        fields = [
            'id',
            'income_entry_id',
            'amount',
            'currency',
            'currency_code',
            'paid_at',
            'created_at',
        ]

        read_only_fields = fields


class InvoicePaymentInputSerializer(serializers.Serializer):
    """Данные новой фактической оплаты."""

    received_at = serializers.DateTimeField()

    financial_account = serializers.PrimaryKeyRelatedField(
        queryset=FinancialAccount.objects.all(),
    )

    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=0.01,
    )

    declaration_category = serializers.ChoiceField(
        choices=[
            'cash_register_18',
            'physical_pos_19',
            'cashless_20',
            'other_21',
        ],
        required=False,
        allow_null=True,
    )

    tax_period_deadline = serializers.DateField(
        required=True,
    )

    payment_method = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default='',
    )

    manual_rate_value = serializers.DecimalField(
        max_digits=20,
        decimal_places=10,
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
        allow_blank=False,
        default='manual',
    )

    ready_amount_gel = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=0.01,
        required=False,
        allow_null=True,
    )

    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )

    def validate_financial_account(
        self,
        financial_account,
    ):
        request = self.context.get('request')

        if request and financial_account.user_id != request.user.id:
            raise serializers.ValidationError('Финансовый счёт принадлежит другому пользователю.')

        return financial_account


class InvoiceSerializer(serializers.ModelSerializer):
    """Сериализатор инвойса."""

    items = InvoiceItemInputSerializer(
        many=True,
        write_only=True,
        required=True,
    )

    invoice_items = InvoiceItemSerializer(
        many=True,
        read_only=True,
    )

    payments = InvoicePaymentSerializer(
        many=True,
        read_only=True,
    )

    financial_account = serializers.PrimaryKeyRelatedField(
        queryset=FinancialAccount.objects.all(),
        write_only=True,
    )

    counterparty = serializers.PrimaryKeyRelatedField(
        queryset=Counterparty.objects.all(),
    )

    currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.filter(
            is_active=True,
        ),
    )

    class Meta:
        model = Invoice

        fields = [
            'id',
            'number',
            'issue_date',
            'service_period_start',
            'service_period_end',
            'due_date',
            'currency',
            'language',
            'status',
            'counterparty',
            'financial_account',
            'items',
            'invoice_items',
            'payments',
            'seller_snapshot',
            'buyer_snapshot',
            'payment_details_snapshot',
            'subtotal',
            'discount_amount',
            'extra_charge_amount',
            'total_amount',
            'tax_note',
            'tax_reference_amount',
            'payment_purpose',
            'notes',
            'pdf_file',
            'pdf_checksum',
            'generated_at',
            'sent_at',
            'paid_at',
            'cancelled_at',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'number',
            'status',
            'seller_snapshot',
            'buyer_snapshot',
            'payment_details_snapshot',
            'subtotal',
            'total_amount',
            'pdf_file',
            'pdf_checksum',
            'generated_at',
            'sent_at',
            'paid_at',
            'cancelled_at',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        request = self.context.get('request')

        if not request:
            return attrs

        user = request.user

        counterparty = attrs.get('counterparty')

        financial_account = attrs.get('financial_account')

        if counterparty and counterparty.user_id != user.id:
            raise serializers.ValidationError(
                {'counterparty': ('Контрагент принадлежит другому пользователю.')}
            )

        if financial_account and financial_account.user_id != user.id:
            raise serializers.ValidationError(
                {'financial_account': ('Финансовый счёт принадлежит другому пользователю.')}
            )

        return attrs
