import hmac
import logging
import requests

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import (
    VersionedTokenObtainPairSerializer,
)
from telegram_integration.models import (
    TelegramConnection,
)
from telegram_integration.security import (
    TelegramInitDataError,
    TelegramInitDataVerifier,
)
from telegram_integration.serializers import (
    TelegramInitDataSerializer,
    TelegramWebhookResponseSerializer,
    TelegramWebhookSerializer,
)
from telegram_integration.bot import (
    TelegramBotClient,
)


logger = logging.getLogger(__name__)


def connection_data(connection):
    return {
        'telegram_user_id': (connection.telegram_user_id),
        'telegram_chat_id': (connection.telegram_chat_id),
        'username': connection.username,
        'first_name': (connection.first_name),
        'last_name': connection.last_name,
        'language_code': (connection.language_code),
        'is_active': connection.is_active,
        'linked_at': connection.linked_at,
    }


class TelegramLinkAPIView(APIView):
    """Привязка Telegram к аккаунту."""

    serializer_class = TelegramInitDataSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = TelegramInitDataSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            verified = TelegramInitDataVerifier.verify(serializer.validated_data['init_data'])

        except TelegramInitDataError as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=(status.HTTP_400_BAD_REQUEST),
            )

        telegram_user = verified['user']

        telegram_user_id = telegram_user['id']

        foreign_connection = (
            TelegramConnection.objects.filter(telegram_user_id=(telegram_user_id))
            .exclude(user=request.user)
            .exists()
        )

        if foreign_connection:
            return Response(
                {'detail': ('Этот Telegram уже связан с другим аккаунтом.')},
                status=(status.HTTP_409_CONFLICT),
            )

        connection, _ = TelegramConnection.objects.update_or_create(
            user=request.user,
            defaults={
                'telegram_user_id': (telegram_user_id),
                'telegram_chat_id': (telegram_user_id),
                'username': (
                    telegram_user.get(
                        'username',
                        '',
                    )
                ),
                'first_name': (
                    telegram_user.get(
                        'first_name',
                        '',
                    )
                ),
                'last_name': (
                    telegram_user.get(
                        'last_name',
                        '',
                    )
                ),
                'language_code': (
                    telegram_user.get(
                        'language_code',
                        '',
                    )
                ),
                'is_active': True,
                'last_seen_at': (timezone.now()),
            },
        )

        return Response(
            {'data': (connection_data(connection))},
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        (TelegramConnection.objects.filter(user=request.user).delete())

        return Response(status=(status.HTTP_204_NO_CONTENT))


class TelegramMiniAppAuthAPIView(APIView):
    """JWT-вход через Telegram Mini App."""

    serializer_class = TelegramInitDataSerializer

    permission_classes = [
        AllowAny,
    ]

    authentication_classes = []

    def post(self, request):
        serializer = TelegramInitDataSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            verified = TelegramInitDataVerifier.verify(serializer.validated_data['init_data'])

        except TelegramInitDataError as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=(status.HTTP_400_BAD_REQUEST),
            )

        telegram_user = verified['user']

        connection = (
            TelegramConnection.objects.select_related('user')
            .filter(
                telegram_user_id=(telegram_user['id']),
                is_active=True,
                user__is_active=True,
            )
            .first()
        )

        if connection is None:
            return Response(
                {'detail': ('Telegram не связан с аккаунтом.')},
                status=(status.HTTP_401_UNAUTHORIZED),
            )

        connection.last_seen_at = timezone.now()

        connection.save(
            update_fields=[
                'last_seen_at',
            ]
        )

        refresh = VersionedTokenObtainPairSerializer.get_token(connection.user)

        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class TelegramWebhookAPIView(APIView):
    """Webhook Telegram Bot API."""

    permission_classes = [
        AllowAny,
    ]

    authentication_classes = []

    @extend_schema(
        tags=['Telegram'],
        auth=[],
        request=TelegramWebhookSerializer,
        responses={200: (TelegramWebhookResponseSerializer)},
    )
    def post(self, request):
        configured_secret = settings.TELEGRAM_WEBHOOK_SECRET

        if configured_secret:
            received_secret = request.headers.get(
                ('X-Telegram-Bot-Api-Secret-Token'),
                '',
            )

            if not hmac.compare_digest(
                configured_secret,
                received_secret,
            ):
                return Response(
                    {'detail': ('Неверный webhook secret.')},
                    status=(status.HTTP_403_FORBIDDEN),
                )

        update = request.data

        message = update.get('message') or update.get('edited_message') or {}

        text = message.get('text', '')

        chat_id = chat.get('id')

        if (
            chat_id is not None
            and text.startswith('/start')
        ):
            try:
                TelegramBotClient().send_start_message(
                    chat_id=chat_id,
                )
            except (
                requests.RequestException,
                RuntimeError,
            ) as error:
                logger.warning(
                    'Telegram sendMessage failed: %s',
                    error,
                )

        telegram_user = message.get('from') or {}

        chat = message.get('chat') or {}

        telegram_user_id = telegram_user.get('id')

        if telegram_user_id:
            connection = TelegramConnection.objects.filter(
                telegram_user_id=(telegram_user_id)
            ).first()

            if connection:
                chat_id = chat.get('id')

                if chat_id is not None:
                    (connection.telegram_chat_id) = chat_id

                connection.last_seen_at = timezone.now()

                connection.save(
                    update_fields=[
                        'telegram_chat_id',
                        'last_seen_at',
                    ]
                )

        return Response(
            {
                'ok': True,
            },
            status=status.HTTP_200_OK,
        )
