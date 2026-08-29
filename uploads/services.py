from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.utils import timezone


class FileDownloadLinkService:
    """Подписанные временные ссылки."""

    SALT = 'uploads.download'

    @classmethod
    def create_token(
        cls,
        *,
        user_file,
        expires_in_seconds=None,
    ):
        if expires_in_seconds is None:
            expires_in_seconds = settings.FILE_DOWNLOAD_LINK_TTL

        expires_at = timezone.now() + timedelta(seconds=(expires_in_seconds))

        token = signing.dumps(
            {
                'file_id': (user_file.id),
                'expires_at': int(expires_at.timestamp()),
            },
            salt=cls.SALT,
        )

        return {
            'token': token,
            'expires_at': expires_at,
        }

    @classmethod
    def validate_token(
        cls,
        token,
    ):
        try:
            data = signing.loads(
                token,
                salt=cls.SALT,
            )

        except signing.BadSignature as error:
            raise ValueError('Ссылка недействительна.') from error

        file_id = data.get('file_id')

        expires_at = data.get('expires_at')

        if not file_id or not expires_at:
            raise ValueError('Ссылка недействительна.')

        now_timestamp = int(timezone.now().timestamp())

        if now_timestamp >= int(expires_at):
            raise ValueError('Срок действия ссылки истёк.')

        return int(file_id)
