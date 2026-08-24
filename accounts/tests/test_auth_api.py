from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import (
    urlsafe_base64_encode,
)
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthAPITests(APITestCase):
    """Тесты JWT-авторизации."""

    def setUp(self):
        self.email = 'user@example.com'
        self.password = 'StrongPass123!abc'

        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
        )

        self.register_url = reverse('auth-register')

        self.login_url = reverse('auth-login')

        self.refresh_url = reverse('auth-token-refresh')

        self.logout_url = reverse('auth-logout')

        self.me_url = reverse('auth-me')

        self.password_reset_url = reverse('auth-password-reset')

        self.password_reset_confirm_url = reverse('auth-password-reset-confirm')

    def _login(self):
        response = self.client.post(
            self.login_url,
            {
                'email': self.email,
                'password': self.password,
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

        return response.data

    def _authenticate(
        self,
        access,
    ):
        self.client.credentials(HTTP_AUTHORIZATION=(f'Bearer {access}'))

    def test_register(self):
        response = self.client.post(
            self.register_url,
            {
                'email': ('new@example.com'),
                'password': ('AnotherPass123!abc'),
                'password_confirm': ('AnotherPass123!abc'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(User.objects.filter(email='new@example.com').exists())

        self.assertNotIn(
            'password',
            response.data,
        )

    def test_duplicate_email_is_rejected(
        self,
    ):
        response = self.client.post(
            self.register_url,
            {
                'email': self.email,
                'password': ('AnotherPass123!abc'),
                'password_confirm': ('AnotherPass123!abc'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_login_returns_tokens(self):
        data = self._login()

        self.assertTrue(data['access'])

        self.assertTrue(data['refresh'])

    def test_me_requires_authentication(
        self,
    ):
        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_me_returns_current_user(
        self,
    ):
        tokens = self._login()

        self._authenticate(tokens['access'])

        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['email'],
            self.email,
        )

        self.assertEqual(
            response.data['id'],
            self.user.id,
        )

    def test_refresh_returns_new_tokens(
        self,
    ):
        tokens = self._login()

        response = self.client.post(
            self.refresh_url,
            {
                'refresh': (tokens['refresh']),
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

    def test_logout_invalidates_old_access(
        self,
    ):
        tokens = self._login()

        self._authenticate(tokens['access'])

        response = self.client.post(
            self.logout_url,
            {
                'refresh': (tokens['refresh']),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.token_version,
            1,
        )

    def test_logout_invalidates_refresh(
        self,
    ):
        tokens = self._login()

        self._authenticate(tokens['access'])

        response = self.client.post(
            self.logout_url,
            {
                'refresh': (tokens['refresh']),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.client.credentials()

        response = self.client.post(
            self.refresh_url,
            {
                'refresh': (tokens['refresh']),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_password_reset_does_not_reveal_email(
        self,
    ):
        existing_response = self.client.post(
            self.password_reset_url,
            {
                'email': self.email,
            },
            format='json',
        )

        unknown_response = self.client.post(
            self.password_reset_url,
            {
                'email': ('unknown@example.com'),
            },
            format='json',
        )

        self.assertEqual(
            existing_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            unknown_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            existing_response.data,
            unknown_response.data,
        )

    def test_password_reset_confirm_changes_password_and_revokes_jwt(
        self,
    ):
        tokens = self._login()

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        token = default_token_generator.make_token(self.user)

        new_password = 'NewStrongPass456!abc'

        response = self.client.post(
            self.password_reset_confirm_url,
            {
                'uid': uid,
                'token': token,
                'new_password': (new_password),
                'new_password_confirm': (new_password),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertTrue(self.user.check_password(new_password))

        self.assertEqual(
            self.user.token_version,
            1,
        )

        self._authenticate(tokens['access'])

        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.client.credentials()

        response = self.client.post(
            self.login_url,
            {
                'email': self.email,
                'password': self.password,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        response = self.client.post(
            self.login_url,
            {
                'email': self.email,
                'password': new_password,
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

    def test_wrong_password_is_rejected(
        self,
    ):
        response = self.client.post(
            self.login_url,
            {
                'email': self.email,
                'password': 'WrongPassword!',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
