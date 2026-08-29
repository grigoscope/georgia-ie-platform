from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from uploads.models import UserFile


class UserFileSerializer(serializers.ModelSerializer):
    """Загрузка файла."""

    file = serializers.FileField(
        write_only=True,
    )

    class Meta:
        model = UserFile

        fields = [
            'id',
            'file',
            'original_name',
            'content_type',
            'size',
            'related_object_type',
            'related_object_id',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'original_name',
            'content_type',
            'size',
            'created_at',
        ]

    def validate_file(
        self,
        uploaded_file,
    ):
        if uploaded_file.size <= 0:
            raise serializers.ValidationError('Файл пуст.')

        if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(('Размер файла превышает допустимый лимит.'))

        return uploaded_file

    def create(
        self,
        validated_data,
    ):
        request = self.context['request']

        uploaded_file = validated_data['file']

        return UserFile.objects.create(
            user=request.user,
            file=uploaded_file,
            original_name=Path(uploaded_file.name).name,
            content_type=(uploaded_file.content_type or ''),
            size=uploaded_file.size,
            related_object_type=(
                validated_data.get(
                    'related_object_type',
                    '',
                )
            ),
            related_object_id=(validated_data.get('related_object_id')),
        )


class DownloadLinkSerializer(serializers.Serializer):
    expires_in_seconds = serializers.IntegerField(
        min_value=60,
        max_value=86400,
        required=False,
    )
