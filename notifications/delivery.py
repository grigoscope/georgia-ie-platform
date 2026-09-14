import requests
from django.db import transaction
from django.utils import timezone

from notifications.models import (
    Notification,
    NotificationSettings,
)
from telegram_integration.bot import (
    TelegramBotClient,
)
from telegram_integration.models import (
    TelegramConnection,
)


class TemporaryTelegramDeliveryError(
    RuntimeError,
):
    pass


class PermanentTelegramDeliveryError(
    RuntimeError,
):
    pass


class NotificationDeliveryService:
    @classmethod
    def deliver_telegram(
        cls,
        *,
        notification_id,
    ):
        with transaction.atomic():
            notification = (
                Notification.objects
                .select_for_update()
                .select_related('user')
                .get(pk=notification_id)
            )

            if notification.telegram_sent_at:
                return {
                    'status': 'already_sent',
                    'notification_id':
                        notification.pk,
                }

            if notification.delivery_status == 'sending':
                return {
                    'status': 'already_processing',
                    'notification_id':
                        notification.pk,
                }

            if not notification.user.is_active:
                return cls._skip(
                    notification,
                    'Пользователь неактивен.',
                )

            settings_obj = (
                NotificationSettings.objects
                .filter(
                    user=notification.user,
                )
                .first()
            )

            if (
                settings_obj is None
                or not settings_obj.telegram_enabled
            ):
                return cls._skip(
                    notification,
                    'Telegram-уведомления отключены.',
                )

            connection = (
                TelegramConnection.objects
                .filter(
                    user=notification.user,
                    is_active=True,
                )
                .first()
            )

            if connection is None:
                return cls._skip(
                    notification,
                    'Telegram не подключён.',
                )

            chat_id = (
                connection.telegram_chat_id
            )

            title = notification.title
            message = notification.message

            notification.delivery_status = (
                'sending'
            )

            notification.error_message = ''

            notification.save(
                update_fields=[
                    'delivery_status',
                    'error_message',
                ],
            )

        text = (
            f'{title}\n\n'
            f'{message}'
        )

        try:
            TelegramBotClient().send_message(
                chat_id=chat_id,
                text=text,
            )

        except Exception as error:
            if cls.is_temporary_error(
                error,
            ):
                cls._mark_retrying(
                    notification_id,
                    error,
                )

                raise (
                    TemporaryTelegramDeliveryError(
                        str(error)
                    )
                ) from error

            cls._mark_failed(
                notification_id,
                error,
            )

            raise (
                PermanentTelegramDeliveryError(
                    str(error)
                )
            ) from error

        with transaction.atomic():
            notification = (
                Notification.objects
                .select_for_update()
                .get(pk=notification_id)
            )

            if notification.telegram_sent_at:
                return {
                    'status': 'already_sent',
                    'notification_id':
                        notification.pk,
                }

            notification.delivery_status = (
                'sent'
            )

            notification.telegram_sent_at = (
                timezone.now()
            )

            notification.error_message = ''

            notification.save(
                update_fields=[
                    'delivery_status',
                    'telegram_sent_at',
                    'error_message',
                ],
            )

        return {
            'status': 'sent',
            'notification_id':
                notification.pk,
        }

    @classmethod
    def _mark_retrying(
        cls,
        notification_id,
        error,
    ):
        with transaction.atomic():
            notification = (
                Notification.objects
                .select_for_update()
                .get(pk=notification_id)
            )

            notification.delivery_status = (
                'retrying'
            )

            notification.error_message = (
                str(error)[:2000]
            )

            notification.save(
                update_fields=[
                    'delivery_status',
                    'error_message',
                ],
            )

    @classmethod
    def _mark_failed(
        cls,
        notification_id,
        error,
    ):
        with transaction.atomic():
            notification = (
                Notification.objects
                .select_for_update()
                .get(pk=notification_id)
            )

            notification.delivery_status = (
                'failed'
            )

            notification.error_message = (
                str(error)[:2000]
            )

            notification.save(
                update_fields=[
                    'delivery_status',
                    'error_message',
                ],
            )

    @staticmethod
    def is_temporary_error(error):
        if isinstance(
            error,
            (
                requests.Timeout,
                requests.ConnectionError,
            ),
        ):
            return True

        if isinstance(
            error,
            requests.HTTPError,
        ):
            response = error.response

            if response is None:
                return True

            return (
                response.status_code == 429
                or response.status_code >= 500
            )

        return False

    @staticmethod
    def _skip(
        notification,
        reason,
    ):
        notification.delivery_status = (
            'skipped'
        )

        notification.error_message = reason

        notification.save(
            update_fields=[
                'delivery_status',
                'error_message',
            ],
        )

        return {
            'status': 'skipped',
            'notification_id':
                notification.pk,
            'reason': reason,
        }
