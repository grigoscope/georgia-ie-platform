from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers

from accounts.models import EntrepreneurProfile


class EntrepreneurProfileSerializer(serializers.ModelSerializer):
    """Профиль предпринимателя."""

    email = serializers.EmailField(
        source='public_email',
        required=False,
        allow_blank=True,
    )

    telegram_connected = serializers.SerializerMethodField()

    signature_url = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = EntrepreneurProfile

        fields = [
            'business_name',
            'entrepreneur_status',
            'tin',
            'legal_address',
            'email',
            'phone',
            'tax_rate',
            'accounting_start_date',
            'timezone',
            'language',
            'invoice_prefix',
            'next_invoice_number',
            'telegram_connected',
            'signature_url',
            'logo_url',
        ]

        read_only_fields = [
            'next_invoice_number',
            'telegram_connected',
            'signature_url',
            'logo_url',
        ]

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise serializers.ValidationError('Неизвестный часовой пояс.') from error

        return value

    def get_telegram_connected(
        self,
        profile,
    ):
        connection = getattr(
            profile.user,
            'telegram_connection',
            None,
        )

        return bool(connection and connection.is_active)

    def get_signature_url(
        self,
        profile,
    ):
        if not profile.signature_file:
            return None

        request = self.context.get('request')

        url = profile.signature_file.url

        if request:
            return request.build_absolute_uri(url)

        return url

    def get_logo_url(
        self,
        profile,
    ):
        if not profile.logo_file:
            return None

        request = self.context.get('request')

        url = profile.logo_file.url

        if request:
            return request.build_absolute_uri(url)

        return url


class ProfileImageUploadSerializer(serializers.Serializer):
    """Загрузка изображения профиля."""

    file = serializers.ImageField(
        write_only=True,
    )

    def validate_file(
        self,
        value,
    ):
        max_size = 5 * 1024 * 1024

        if value.size > max_size:
            raise serializers.ValidationError('Размер файла не должен превышать 5 МБ.')

        return value
