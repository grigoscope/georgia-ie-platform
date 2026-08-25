from decimal import Decimal

from rest_framework import serializers

from taxes.models import TaxPeriod


class TaxPeriodSerializer(serializers.ModelSerializer):
    """Налоговый период."""

    class Meta:
        model = TaxPeriod

        fields = [
            'id',
            'year',
            'month',
            'field_15',
            'field_17',
            'field_18',
            'field_19',
            'field_20',
            'field_21',
            'tax_rate',
            'field_26',
            'calculation_status',
            'declaration_status',
            'submitted_at',
            'submission_comment',
            'submission_confirmation',
            'payment_status',
            'paid_at',
            'paid_amount',
            'payment_comment',
            'payment_confirmation',
            'deadline',
            'is_overdue',
            'changed_after_submission',
            'calculated_at',
            'created_at',
            'updated_at',
        ]

        read_only_fields = fields


class TaxPeriodGenerateSerializer(serializers.Serializer):
    year = serializers.IntegerField(
        min_value=2000,
        max_value=2200,
    )

    month = serializers.IntegerField(
        min_value=1,
        max_value=12,
    )


class TaxRatePreviewSerializer(serializers.Serializer):
    tax_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00'),
    )


class MarkSubmittedSerializer(serializers.Serializer):
    submitted_at = serializers.DateTimeField(
        required=False,
    )

    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )

    confirmation_file = serializers.FileField(
        required=False,
        allow_null=True,
    )


class MarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateTimeField(
        required=False,
    )

    paid_amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal('0.00'),
    )

    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )

    confirmation_file = serializers.FileField(
        required=False,
        allow_null=True,
    )
