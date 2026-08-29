from django.contrib.auth import (
    get_user_model,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from audit.models import AuditLog

User = get_user_model()


class AuditV1APITests(APITestCase):
    """Stage 4 Audit API."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='StrongPass123!',
        )

        self.client.force_authenticate(user=self.user)

        self.url = reverse('v1-audit-list')

    def test_requires_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_only_own_logs_are_visible(
        self,
    ):
        own_log = AuditLog.objects.create(
            user=self.user,
            actor=self.user,
            action='create',
            object_type='IncomeEntry',
            object_id=10,
        )

        AuditLog.objects.create(
            user=self.other_user,
            actor=self.other_user,
            action='create',
            object_type='IncomeEntry',
            object_id=20,
        )

        response = self.client.get(self.url)

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
            own_log.id,
        )

    def test_filter_by_action(
        self,
    ):
        AuditLog.objects.create(
            user=self.user,
            actor=self.user,
            action='create',
            object_type='Invoice',
            object_id=1,
        )

        AuditLog.objects.create(
            user=self.user,
            actor=self.user,
            action='delete',
            object_type='Invoice',
            object_id=2,
        )

        response = self.client.get(
            self.url,
            {
                'action': 'delete',
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
            response.data['results'][0]['action'],
            'delete',
        )

    def test_audit_is_paginated(
        self,
    ):
        for number in range(25):
            AuditLog.objects.create(
                user=self.user,
                actor=self.user,
                action='test',
                object_type='TestObject',
                object_id=number + 1,
            )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['count'],
            25,
        )

        self.assertEqual(
            len(response.data['results']),
            20,
        )
