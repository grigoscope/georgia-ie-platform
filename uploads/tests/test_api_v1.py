import tempfile
from time import time

from django.contrib.auth import (
    get_user_model,
)
from django.core import signing
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from uploads.models import UserFile
from uploads.services import (
    FileDownloadLinkService,
)

User = get_user_model()


class FilesV1APITests(APITestCase):
    """Stage 4 Files API."""

    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()

        self.media_override = override_settings(
            MEDIA_ROOT=(self.temp_media.name),
            MAX_UPLOAD_SIZE=(10 * 1024 * 1024),
            FILE_DOWNLOAD_LINK_TTL=900,
        )

        self.media_override.enable()

        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='StrongPass123!',
        )

        self.client.force_authenticate(user=self.user)

        self.upload_url = reverse('v1-file-upload')

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

    @staticmethod
    def _file():
        return SimpleUploadedFile(
            'document.txt',
            b'hello world',
            content_type='text/plain',
        )

    def _upload(self):
        response = self.client.post(
            self.upload_url,
            {
                'file': self._file(),
            },
            format='multipart',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        return UserFile.objects.get(id=response.data['id'])

    def test_upload_requires_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.upload_url,
            {
                'file': self._file(),
            },
            format='multipart',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_upload_file(self):
        user_file = self._upload()

        self.assertEqual(
            user_file.user,
            self.user,
        )

        self.assertEqual(
            user_file.original_name,
            'document.txt',
        )

        self.assertEqual(
            user_file.content_type,
            'text/plain',
        )

        self.assertEqual(
            user_file.size,
            11,
        )

    def test_create_download_link(
        self,
    ):
        user_file = self._upload()

        response = self.client.post(
            reverse(
                'v1-file-download-link',
                args=[user_file.id],
            ),
            {},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            'url',
            response.data['data'],
        )

        self.assertIn(
            'expires_at',
            response.data['data'],
        )

    def test_foreign_file_is_hidden(
        self,
    ):
        foreign_file = UserFile.objects.create(
            user=self.other_user,
            file=SimpleUploadedFile(
                'foreign.txt',
                b'foreign',
            ),
            original_name=('foreign.txt'),
            content_type='text/plain',
            size=7,
        )

        response = self.client.post(
            reverse(
                'v1-file-download-link',
                args=[foreign_file.id],
            ),
            {},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_public_download(
        self,
    ):
        user_file = self._upload()

        result = FileDownloadLinkService.create_token(user_file=user_file)

        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse(
                'public-file-download',
                kwargs={
                    'token': (result['token']),
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response['Content-Type'],
            'text/plain',
        )

    def test_expired_link_is_rejected(
        self,
    ):
        user_file = self._upload()

        token = signing.dumps(
            {
                'file_id': (user_file.id),
                'expires_at': int(time()) - 10,
            },
            salt=(FileDownloadLinkService.SALT),
        )

        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse(
                'public-file-download',
                kwargs={
                    'token': token,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_tampered_link_is_rejected(
        self,
    ):
        user_file = self._upload()

        result = FileDownloadLinkService.create_token(user_file=user_file)

        token = result['token'] + 'broken'

        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse(
                'public-file-download',
                kwargs={
                    'token': token,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_file(
        self,
    ):
        user_file = self._upload()

        response = self.client.delete(
            reverse(
                'v1-file-delete',
                args=[user_file.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(UserFile.objects.filter(id=user_file.id).exists())
