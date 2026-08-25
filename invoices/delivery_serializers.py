from rest_framework import serializers


class InvoiceEmailSerializer(serializers.Serializer):
    recipient = serializers.EmailField(
        required=False,
    )


class InvoiceShareSerializer(serializers.Serializer):
    expires_in_hours = serializers.IntegerField(
        min_value=1,
        max_value=168,
        required=False,
        default=24,
    )
