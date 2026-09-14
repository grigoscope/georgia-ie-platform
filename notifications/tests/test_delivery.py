from unittest.mock import patch

import requests
from django.test import TestCase

from accounts.models import User
from notifications.delivery import (
    NotificationDeliveryService,
    PermanentTelegramDeliveryError,
    TemporaryTelegramDeliveryError,
)
from notifications.models import (
    Notification,
    NotificationSettings,
)
from telegram_integration.models import (
    TelegramConnection,
)


class TelegramDeliveryTests(
    TestCase,
):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                email='telegram-delivery@example.com',
                password='Password123!',
            )
        )

        self.settings_obj = (
            NotificationSettings
            .objects
            .create(
                user=self.user,
                telegram_enabled=True,
            )
        )

        self.connection = (
            TelegramConnection
            .objects
            .create(
                user=self.user,
                telegram_user_id=111,
                telegram_chat_id=222,
                is_active=True,
            )
        )

        self.notification = (
            Notification.objects.create(
                user=self.user,
                type='tax_reminder',
                title='Налог',
                message='Проверьте период.',
                delivery_status='pending',
                deduplication_key=(
                    'tax:test:telegram'
                ),
            )
        )

    @patch(
        'notifications.delivery.'
        'TelegramBotClient.send_message'
    )
    def test_successful_delivery(
        self,
        send_message,
    ):
        send_message.return_value = {
            'ok': True,
        }

        result = (
            NotificationDeliveryService
            .deliver_telegram(
                notification_id=
                    self.notification.pk,
            )
        )

        self.notification.refresh_from_db()

        self.assertEqual(
            result['status'],
            'sent',
        )

        self.assertEqual(
            self.notification
            .delivery_status,
            'sent',
        )

        self.assertIsNotNone(
            self.notification
            .telegram_sent_at,
        )

        send_message.assert_called_once()

    @patch(
        'notifications.delivery.'
        'TelegramBotClient.send_message'
    )
    def test_repeat_delivery_is_not_duplicated(
        self,
        send_message,
    ):
        send_message.return_value = {
            'ok': True,
        }

        NotificationDeliveryService.deliver_telegram(
            notification_id=
                self.notification.pk,
        )

        result = (
            NotificationDeliveryService
            .deliver_telegram(
                notification_id=
                    self.notification.pk,
            )
        )

        self.assertEqual(
            result['status'],
            'already_sent',
        )

        self.assertEqual(
            send_message.call_count,
            1,
        )

    def test_disabled_channel_is_skipped(
        self,
    ):
        self.settings_obj.telegram_enabled = (
            False
        )

        self.settings_obj.save(
            update_fields=[
                'telegram_enabled',
            ],
        )

        result = (
            NotificationDeliveryService
            .deliver_telegram(
                notification_id=
                    self.notification.pk,
            )
        )

        self.notification.refresh_from_db()

        self.assertEqual(
            result['status'],
            'skipped',
        )

        self.assertEqual(
            self.notification
            .delivery_status,
            'skipped',
        )

    @patch(
        'notifications.delivery.'
        'TelegramBotClient.send_message'
    )
    def test_timeout_is_temporary_error(
        self,
        send_message,
    ):
        send_message.side_effect = (
            requests.Timeout(
                'timeout'
            )
        )

        with self.assertRaises(
            TemporaryTelegramDeliveryError,
        ):
            (
                NotificationDeliveryService
                .deliver_telegram(
                    notification_id=
                        self.notification.pk,
                )
            )

        self.notification.refresh_from_db()

        self.assertEqual(
            self.notification
            .delivery_status,
            'retrying',
        )

    @patch(
        'notifications.delivery.'
        'TelegramBotClient.send_message'
    )
    def test_permanent_error_is_saved(
        self,
        send_message,
    ):
        send_message.side_effect = (
            RuntimeError(
                'Telegram rejected request'
            )
        )

        with self.assertRaises(
            PermanentTelegramDeliveryError,
        ):
            (
                NotificationDeliveryService
                .deliver_telegram(
                    notification_id=
                        self.notification.pk,
                )
            )

        self.notification.refresh_from_db()

        self.assertEqual(
            self.notification
            .delivery_status,
            'failed',
        )

        self.assertIn(
            'Telegram rejected request',
            self.notification
            .error_message,
        )
