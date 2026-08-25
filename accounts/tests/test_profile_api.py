import base64
import tempfile
from decimal import Decimal

from django.contrib.auth import (
    get_user_model,
)
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import (
    override_settings,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import (
    EntrepreneurProfile,
)
from telegram_integration.models import (
    TelegramConnection,
)

User = get_user_model()


class ProfileAPITests(APITestCase):
    """Тесты API профиля."""

    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()

        self.media_override = override_settings(MEDIA_ROOT=(self.temp_media.name))

        self.media_override.enable()

        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
        )

        self.profile = EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            tin='123456789',
            tax_rate=Decimal('1.00'),
        )

        self.profile_url = reverse('profile')

        self.signature_url = reverse('profile-signature')

        self.logo_url = reverse('profile-logo')

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

    def _authenticate(self):
        self.client.force_authenticate(user=self.user)

    @staticmethod
    def _image():
        png = base64.b64decode(
            (
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB'
                'CAQAAAC1HAwCAAAAC0lEQVR42mNk'
                'YAAAAAYAAjCB0C8AAAAASUVORK5CYII='
            )
        )

        return SimpleUploadedFile(
            'image.png',
            png,
            content_type='image/png',
        )

    def test_profile_requires_authentication(
        self,
    ):
        response = self.client.get(self.profile_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_get_profile(self):
        self._authenticate()

        response = self.client.get(self.profile_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['business_name'],
            'Test Business',
        )

        self.assertEqual(
            response.data['tin'],
            '123456789',
        )

        self.assertFalse(response.data['telegram_connected'])

    def test_patch_profile(self):
        self._authenticate()

        response = self.client.patch(
            self.profile_url,
            {
                'business_name': ('Updated Business'),
                'email': ('public@example.com'),
                'timezone': ('Asia/Tbilisi'),
                'language': 'en',
                'invoice_prefix': 'GB-',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.business_name,
            'Updated Business',
        )

        self.assertEqual(
            self.profile.public_email,
            'public@example.com',
        )

        self.assertEqual(
            self.profile.invoice_prefix,
            'GB-',
        )

    def test_invalid_timezone_is_rejected(
        self,
    ):
        self._authenticate()

        response = self.client.patch(
            self.profile_url,
            {
                'timezone': ('Planet/Mars'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_next_invoice_number_is_read_only(
        self,
    ):
        self._authenticate()

        response = self.client.patch(
            self.profile_url,
            {
                'next_invoice_number': 999,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.next_invoice_number,
            1,
        )

    def test_telegram_connected(
        self,
    ):
        TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=123456,
            telegram_chat_id=123456,
            username='testuser',
            is_active=True,
        )

        self._authenticate()

        response = self.client.get(self.profile_url)

        self.assertTrue(response.data['telegram_connected'])

    def test_upload_and_delete_signature(
        self,
    ):
        self._authenticate()

        response = self.client.post(
            self.signature_url,
            {
                'file': self._image(),
            },
            format='multipart',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.profile.refresh_from_db()

        self.assertTrue(self.profile.signature_file)

        response = self.client.delete(self.signature_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.profile.refresh_from_db()

        self.assertFalse(self.profile.signature_file)

    def test_upload_and_delete_logo(
        self,
    ):
        self._authenticate()

        response = self.client.post(
            self.logo_url,
            {
                'file': self._image(),
            },
            format='multipart',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.profile.refresh_from_db()

        self.assertTrue(self.profile.logo_file)

        response = self.client.delete(self.logo_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.profile.refresh_from_db()

        self.assertFalse(self.profile.logo_file)

    def test_profile_can_be_created_by_patch(
        self,
    ):
        new_user = User.objects.create_user(
            email='new@example.com',
            password='StrongPass123!',
        )

        self.client.force_authenticate(user=new_user)

        response = self.client.patch(
            self.profile_url,
            {
                'business_name': ('New Business'),
                'tin': '999888777',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            EntrepreneurProfile.objects.filter(
                user=new_user,
                business_name='New Business',
                tin='999888777',
            ).exists()
        )
