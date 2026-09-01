from django.contrib.auth import (
    get_user_model,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from notifications.models import (
    Notification,
    NotificationSettings,
)

User = get_user_model()


class NotificationV1APITests(APITestCase):
    """Stage 4 Notifications API."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='StrongPass123!',
        )

        self.notification = Notification.objects.create(
            user=self.user,
            type='tax_reminder',
            title='Tax reminder',
            message='Submit declaration',
            related_object_type=('TaxPeriod'),
            related_object_id=10,
            action_url='/taxes/2026/8/',
        )

        self.other_notification = Notification.objects.create(
            user=self.other_user,
            type='invoice_reminder',
            title='Foreign notification',
            message='Foreign data',
        )

        self.client.force_authenticate(user=self.user)

        self.list_url = reverse('v1-notification-list')

        self.settings_url = reverse('v1-notification-settings')

    def test_notifications_require_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_list_contains_only_own_notifications(
        self,
    ):
        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['count'],
            1,
        )

        self.assertEqual(
            response.data['results'][0]['id'],
            self.notification.id,
        )

    def test_foreign_notification_is_hidden(
        self,
    ):
        response = self.client.get(
            reverse(
                'v1-notification-detail',
                args=[self.other_notification.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_mark_read(
        self,
    ):
        response = self.client.post(
            reverse(
                ('v1-notification-mark-read'),
                args=[self.notification.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.notification.refresh_from_db()

        self.assertIsNotNone(self.notification.read_at)

        self.assertTrue(response.data['is_read'])

    def test_mark_read_is_idempotent(
        self,
    ):
        url = reverse(
            'v1-notification-mark-read',
            args=[self.notification.id],
        )

        first = self.client.post(url)

        self.notification.refresh_from_db()

        first_read_at = self.notification.read_at

        second = self.client.post(url)

        self.notification.refresh_from_db()

        self.assertEqual(
            first.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            self.notification.read_at,
            first_read_at,
        )

    def test_mark_all_read(
        self,
    ):
        second_notification = Notification.objects.create(
            user=self.user,
            type='test',
            title='Second',
            message='Second message',
        )

        response = self.client.post(reverse(('v1-notification-mark-all-read')))

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['data']['updated'],
            2,
        )

        self.notification.refresh_from_db()
        second_notification.refresh_from_db()

        self.assertIsNotNone(self.notification.read_at)

        self.assertIsNotNone(second_notification.read_at)

        self.other_notification.refresh_from_db()

        self.assertIsNone(self.other_notification.read_at)

    def test_filter_unread(
        self,
    ):
        read_notification = Notification.objects.create(
            user=self.user,
            type='test',
            title='Read',
            message='Already read',
        )

        from django.utils import timezone

        read_notification.read_at = timezone.now()

        read_notification.save(
            update_fields=[
                'read_at',
            ]
        )

        response = self.client.get(
            self.list_url,
            {
                'is_read': 'false',
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['count'],
            1,
        )

        self.assertEqual(
            response.data['results'][0]['id'],
            self.notification.id,
        )

    def test_search_notifications(
        self,
    ):
        Notification.objects.create(
            user=self.user,
            type='invoice',
            title='Invoice overdue',
            message='Invoice INV-10',
        )

        response = self.client.get(
            self.list_url,
            {
                'search': 'INV-10',
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['count'],
            1,
        )

    def test_notifications_are_paginated(
        self,
    ):
        for number in range(25):
            Notification.objects.create(
                user=self.user,
                type='test',
                title=(f'Notification {number}'),
                message='Test',
            )

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['count'],
            26,
        )

        self.assertEqual(
            len(response.data['results']),
            20,
        )

    def test_settings_are_created_automatically(
        self,
    ):
        self.assertFalse(NotificationSettings.objects.filter(user=self.user).exists())

        response = self.client.get(self.settings_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(NotificationSettings.objects.filter(user=self.user).exists())

        self.assertTrue(response.data['internal_enabled'])

        self.assertTrue(response.data['tax_reminders_enabled'])

    def test_update_notification_settings(
        self,
    ):
        response = self.client.patch(
            self.settings_url,
            {
                'telegram_enabled': True,
                'email_enabled': True,
                'send_time': '09:30:00',
                'tax_reminders_enabled': (False),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        settings_object = NotificationSettings.objects.get(user=self.user)

        self.assertTrue(settings_object.telegram_enabled)

        self.assertTrue(settings_object.email_enabled)

        self.assertFalse(settings_object.tax_reminders_enabled)

        self.assertEqual(
            settings_object.send_time.isoformat(),
            '09:30:00',
        )

    def test_settings_require_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.settings_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_notification_settings_route_matches_api_contract(
        self,
    ):
        self.assertEqual(
            self.settings_url,
            ('/api/v1/notification-settings/'),
        )
