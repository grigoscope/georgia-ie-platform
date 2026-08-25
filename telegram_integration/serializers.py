from rest_framework import serializers


class TelegramInitDataSerializer(serializers.Serializer):
    init_data = serializers.CharField(
        trim_whitespace=False,
    )
