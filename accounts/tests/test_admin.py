from django.contrib import admin
from django.contrib.messages.storage.fallback import (
    FallbackStorage,
)
from django.test import (
    RequestFactory,
    TestCase,
)

from accounts.admin import CustomUserAdmin
from accounts.models import (
    EntrepreneurProfile,
    User,
)
from audit.models import AuditLog
from telegram_integration.models import (
    TelegramConnection,
)


class AdminConfigurationTests(
    TestCase,
):
    def setUp(self):
        self.superuser = (
            User.objects.create_superuser(
                email='admin@example.com',
                password='AdminPassword123!',
            )
        )

        self.user = (
            User.objects.create_user(
                email='user@example.com',
                password='UserPassword123!',
            )
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test IE',
            tin='123456789',
        )

        TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=123456,
            telegram_chat_id=123456,
            username='testuser',
            is_active=True,
        )

        self.factory = RequestFactory()

        self.model_admin = (
            CustomUserAdmin(
                User,
                admin.site,
            )
        )

    def make_request(self):
        request = self.factory.post(
            '/admin/accounts/user/',
        )

        request.user = self.superuser
        request.session = {}
        request._messages = (
            FallbackStorage(
                request,
            )
        )

        return request

    def test_required_models_are_registered(
        self,
    ):
        self.assertIn(
            User,
            admin.site._registry,
        )

        self.assertIn(
            EntrepreneurProfile,
            admin.site._registry,
        )

        self.assertIn(
            AuditLog,
            admin.site._registry,
        )

        self.assertIn(
            TelegramConnection,
            admin.site._registry,
        )

    def test_block_user_creates_audit_log(
        self,
    ):
        request = self.make_request()

        self.model_admin.block_users(
            request,
            User.objects.filter(
                pk=self.user.pk,
            ),
        )

        self.user.refresh_from_db()

        self.assertFalse(
            self.user.is_active,
        )

        self.assertTrue(
            AuditLog.objects.filter(
                user=self.user,
                actor=self.superuser,
                action='admin_block_user',
            ).exists()
        )

    def test_unblock_user_creates_audit_log(
        self,
    ):
        self.user.is_active = False
        self.user.save(
            update_fields=[
                'is_active',
            ],
        )

        request = self.make_request()

        self.model_admin.unblock_users(
            request,
            User.objects.filter(
                pk=self.user.pk,
            ),
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.is_active,
        )

        self.assertTrue(
            AuditLog.objects.filter(
                user=self.user,
                actor=self.superuser,
                action='admin_unblock_user',
            ).exists()
        )

    def test_reset_telegram_link_creates_audit_log(
        self,
    ):
        request = self.make_request()

        self.model_admin.reset_telegram_links(
            request,
            User.objects.filter(
                pk=self.user.pk,
            ),
        )

        self.assertFalse(
            TelegramConnection
            .objects
            .filter(
                user=self.user,
            )
            .exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                user=self.user,
                actor=self.superuser,
                action='admin_reset_telegram',
            ).exists()
        )

    def test_bulk_delete_is_disabled(
        self,
    ):
        request = self.make_request()

        actions = (
            self.model_admin
            .get_actions(request)
        )

        self.assertNotIn(
            'delete_selected',
            actions,
        )
