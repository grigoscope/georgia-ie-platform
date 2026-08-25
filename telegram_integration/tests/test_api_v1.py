import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from telegram_integration.models import (
    TelegramConnection,
)

User = get_user_model()


@override_settings(
    TELEGRAM_BOT_TOKEN='123456:TEST_TOKEN',
    TELEGRAM_WEBHOOK_SECRET='test-webhook-secret',
    TELEGRAM_INIT_DATA_MAX_AGE=600,
)
class TelegramV1APITests(APITestCase):
    """Stage 4 Telegram API."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='StrongPass123!',
        )

        self.telegram_user = {
            'id': 123456789,
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'test_user',
            'language_code': 'en',
        }

        self.link_url = reverse('telegram-link')

        self.mini_app_url = reverse('telegram-mini-app-auth')

        self.webhook_url = reverse('telegram-webhook')

    @staticmethod
    def _make_init_data(
        telegram_user,
        *,
        auth_date=None,
        token='123456:TEST_TOKEN',
    ):
        if auth_date is None:
            auth_date = int(time.time())

        data = {
            'auth_date': str(auth_date),
            'query_id': ('AAHdF6IQAAAAAN0XohDhrOrc'),
            'user': json.dumps(
                telegram_user,
                separators=(',', ':'),
                ensure_ascii=False,
            ),
        }

        data_check_string = '\n'.join((f'{key}={value}' for key, value in sorted(data.items())))

        secret_key = hmac.new(
            b'WebAppData',
            token.encode(),
            hashlib.sha256,
        ).digest()

        signature = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        data['hash'] = signature

        return urlencode(data)

    def test_link_requires_authentication(
        self,
    ):
        init_data = self._make_init_data(self.telegram_user)

        response = self.client.post(
            self.link_url,
            {
                'init_data': init_data,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_link_telegram(
        self,
    ):
        self.client.force_authenticate(user=self.user)

        init_data = self._make_init_data(self.telegram_user)

        response = self.client.post(
            self.link_url,
            {
                'init_data': init_data,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        connection = TelegramConnection.objects.get(user=self.user)

        self.assertEqual(
            connection.telegram_user_id,
            123456789,
        )

        self.assertEqual(
            connection.telegram_chat_id,
            123456789,
        )

        self.assertEqual(
            connection.username,
            'test_user',
        )

        self.assertTrue(connection.is_active)

    def test_link_rejects_invalid_signature(
        self,
    ):
        self.client.force_authenticate(user=self.user)

        init_data = self._make_init_data(self.telegram_user)

        init_data = (
            init_data.rsplit(
                'hash=',
                1,
            )[0]
            + 'hash=invalid'
        )

        response = self.client.post(
            self.link_url,
            {
                'init_data': init_data,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(TelegramConnection.objects.exists())

    def test_link_rejects_expired_init_data(
        self,
    ):
        self.client.force_authenticate(user=self.user)

        init_data = self._make_init_data(
            self.telegram_user,
            auth_date=(int(time.time()) - 1000),
        )

        response = self.client.post(
            self.link_url,
            {
                'init_data': init_data,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_telegram_cannot_be_linked_to_two_users(
        self,
    ):
        TelegramConnection.objects.create(
            user=self.other_user,
            telegram_user_id=123456789,
            telegram_chat_id=123456789,
            username='test_user',
        )

        self.client.force_authenticate(user=self.user)

        init_data = self._make_init_data(self.telegram_user)

        response = self.client.post(
            self.link_url,
            {
                'init_data': init_data,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )

        self.assertFalse(TelegramConnection.objects.filter(user=self.user).exists())

    def test_unlink_telegram(
        self,
    ):
        TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_chat_id=123456789,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.link_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(TelegramConnection.objects.filter(user=self.user).exists())

    def test_mini_app_auth_returns_jwt(
        self,
    ):
        TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_chat_id=123456789,
            is_active=True,
        )

        init_data = self._make_init_data(self.telegram_user)

        response = self.client.post(
            self.mini_app_url,
            {
                'init_data': init_data,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            'access',
            response.data,
        )

        self.assertIn(
            'refresh',
            response.data,
        )

        access = response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=(f'Bearer {access}'))

        response = self.client.get(reverse('auth-me'))

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['email'],
            self.user.email,
        )

    def test_mini_app_auth_rejects_unknown_telegram(
        self,
    ):
        init_data = self._make_init_data(self.telegram_user)

        response = self.client.post(
            self.mini_app_url,
            {
                'init_data': init_data,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_inactive_connection_cannot_authenticate(
        self,
    ):
        TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_chat_id=123456789,
            is_active=False,
        )

        init_data = self._make_init_data(self.telegram_user)

        response = self.client.post(
            self.mini_app_url,
            {
                'init_data': init_data,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_webhook_rejects_wrong_secret(
        self,
    ):
        response = self.client.post(
            self.webhook_url,
            {
                'update_id': 1,
            },
            format='json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=('wrong-secret'),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_webhook_updates_chat_id(
        self,
    ):
        connection = TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_chat_id=123456789,
        )

        response = self.client.post(
            self.webhook_url,
            {
                'update_id': 100,
                'message': {
                    'message_id': 10,
                    'from': {
                        'id': 123456789,
                        'first_name': 'Test',
                    },
                    'chat': {
                        'id': 987654321,
                        'type': 'private',
                    },
                    'text': '/start',
                },
            },
            format='json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=('test-webhook-secret'),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        connection.refresh_from_db()

        self.assertEqual(
            connection.telegram_chat_id,
            987654321,
        )

        self.assertIsNotNone(connection.last_seen_at)
