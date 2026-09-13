from django.contrib import admin
from django.contrib.messages.storage.fallback import (
    FallbackStorage,
)
from django.test import (
    RequestFactory,
    TestCase,
)

from accounts.models import User
from audit.models import AuditLog
from invoices.admin import (
    InvoiceItemInline,
)
from invoices.models import Invoice
from notifications.admin import (
    NotificationAdmin,
)
from notifications.models import (
    Notification,
    NotificationSettings,
)
from taxes.admin import TaxPeriodAdmin
from taxes.models import TaxPeriod


class AdvancedAdminTests(TestCase):
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

        self.factory = (
            RequestFactory()
        )

    def make_request(self):
        request = self.factory.post(
            '/admin/',
        )

        request.user = (
            self.superuser
        )

        request.session = {}

        request._messages = (
            FallbackStorage(
                request,
            )
        )

        return request

    def test_models_are_registered(
        self,
    ):
        self.assertIn(
            Invoice,
            admin.site._registry,
        )

        self.assertIn(
            TaxPeriod,
            admin.site._registry,
        )

        self.assertIn(
            Notification,
            admin.site._registry,
        )

        self.assertIn(
            NotificationSettings,
            admin.site._registry,
        )

    def test_tax_status_fields_are_readonly(
        self,
    ):
        model_admin = (
            TaxPeriodAdmin(
                TaxPeriod,
                admin.site,
            )
        )

        readonly = (
            model_admin
            .get_readonly_fields(
                self.make_request(),
            )
        )

        self.assertIn(
            'declaration_status',
            readonly,
        )

        self.assertIn(
            'payment_status',
            readonly,
        )

        self.assertIn(
            'paid_amount',
            readonly,
        )

    def test_invoice_items_are_readonly(
        self,
    ):
        inline = InvoiceItemInline(
            Invoice,
            admin.site,
        )

        self.assertEqual(
            tuple(
                inline.readonly_fields
            ),
            (
                'position',
                'description',
                'quantity',
                'unit',
                'unit_price',
                'line_total',
            ),
        )

        self.assertFalse(
            inline.has_add_permission(
                self.make_request(),
            )
        )

    def test_cancel_pending_notification_creates_audit(
        self,
    ):
        notification = (
            Notification.objects.create(
                user=self.user,
                type='test',
                title='Test',
                message='Test notification',
                delivery_status='pending',
            )
        )

        model_admin = (
            NotificationAdmin(
                Notification,
                admin.site,
            )
        )

        model_admin.cancel_pending(
            self.make_request(),
            Notification.objects.filter(
                pk=notification.pk,
            ),
        )

        notification.refresh_from_db()

        self.assertEqual(
            notification.delivery_status,
            'cancelled',
        )

        self.assertTrue(
            AuditLog.objects.filter(
                user=self.user,
                actor=self.superuser,
                action='admin_cancel_notification',
                object_id=notification.pk,
            ).exists()
        )
