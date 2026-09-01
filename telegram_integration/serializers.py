from rest_framework import serializers


class TelegramInitDataSerializer(serializers.Serializer):
    init_data = serializers.CharField(
        trim_whitespace=False,
    )


class TelegramWebhookSerializer(serializers.Serializer):
    update_id = serializers.IntegerField(required=False)

    message = serializers.JSONField(required=False)

    edited_message = serializers.JSONField(required=False)


class TelegramWebhookResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
