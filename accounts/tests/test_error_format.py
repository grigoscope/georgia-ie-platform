from django.contrib.auth import (
    get_user_model,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

User = get_user_model()


class APIErrorFormatTests(APITestCase):
    """Единый формат ошибок Stage 4."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
        )

    @staticmethod
    def _payload(response):
        """
        Проверяем именно реальный JSON,
        который получает frontend.
        """

        return response.json()

    def test_validation_error_format(
        self,
    ):
        response = self.client.post(
            reverse('auth-register'),
            {
                'email': ('new@example.com'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        data = self._payload(response)

        self.assertIn(
            'error',
            data,
        )

        error = data['error']

        self.assertEqual(
            error['code'],
            'validation_error',
        )

        self.assertIn(
            'message',
            error,
        )

        self.assertIn(
            'fields',
            error,
        )

        self.assertIn(
            'password',
            error['fields'],
        )

        self.assertIn(
            'password_confirm',
            error['fields'],
        )

    def test_unauthenticated_error_format(
        self,
    ):
        response = self.client.get(reverse('auth-me'))

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        data = self._payload(response)

        self.assertEqual(
            data['error']['code'],
            'authentication_error',
        )

        self.assertEqual(
            data['error']['fields'],
            {},
        )

    def test_not_found_error_format(
        self,
    ):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(
                'v1-notification-detail',
                args=[999999],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        data = self._payload(response)

        self.assertEqual(
            data['error']['code'],
            'not_found',
        )

        self.assertIn(
            'message',
            data['error'],
        )

    def test_manual_error_response_is_wrapped(
        self,
    ):
        """
        Важно: проверяем старый ручной
        Response(..., status=404), а не
        только DRF exception.
        """

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse(
                'v1-file-download-link',
                args=[999999],
            ),
            {},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        data = self._payload(response)

        self.assertEqual(
            data,
            {
                'error': {
                    'code': 'not_found',
                    'message': ('Файл не найден.'),
                    'fields': {},
                }
            },
        )

    def test_method_not_allowed_format(
        self,
    ):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse('v1-audit-list'),
            {},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            (status.HTTP_405_METHOD_NOT_ALLOWED),
        )

        data = self._payload(response)

        self.assertEqual(
            data['error']['code'],
            'method_not_allowed',
        )

        self.assertEqual(
            data['error']['fields'],
            {},
        )

    def test_error_has_exact_top_level_shape(
        self,
    ):
        response = self.client.get(reverse('auth-me'))

        data = self._payload(response)

        self.assertEqual(
            set(data.keys()),
            {'error'},
        )

        self.assertEqual(
            set(data['error'].keys()),
            {
                'code',
                'message',
                'fields',
            },
        )
