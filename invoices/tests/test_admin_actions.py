from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from accounts.models import User
from audit.models import AuditLog
from exchange_rates.models import Currency
from finances.models import Counterparty
from invoices.admin import InvoiceAdmin
from invoices.models import Invoice
from telegram_integration.models import TelegramConnection


class InvoiceAdminActionTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPassword123!',
        )

        self.user = User.objects.create_user(
            email='owner@example.com',
            password='UserPassword123!',
        )

        self.currency = Currency.objects.create(
            code='GEL',
            name='Georgian Lari',
            kind='fiat',
            decimal_places=2,
            is_active=True,
        )

        self.counterparty = Counterparty.objects.create(
            user=self.user,
            name='Client',
            type='company',
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            number='INV-1',
            issue_date=date(2026, 9, 13),
            currency=self.currency,
            counterparty=self.counterparty,
            seller_snapshot={},
            buyer_snapshot={},
            payment_details_snapshot={},
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
        )

        TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=123456,
            telegram_chat_id=123456,
            username='owner',
            is_active=True,
        )

        self.factory = RequestFactory()
        self.model_admin = InvoiceAdmin(
            Invoice,
            admin.site,
        )

    def make_request(self):
        request = self.factory.post(
            '/admin/invoices/invoice/',
        )
        request.user = self.superuser
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    @patch(
        'invoices.admin.InvoiceDeliveryService.send_to_telegram',
        return_value={
            'ok': True,
            'result': {
                'message_id': 777,
            },
        },
    )
    def test_send_to_owner_telegram_creates_audit(self, mocked_send):
        self.model_admin.send_to_owner_telegram(
            self.make_request(),
            Invoice.objects.filter(pk=self.invoice.pk),
        )

        mocked_send.assert_called_once()

        audit = AuditLog.objects.filter(
            user=self.user,
            actor=self.superuser,
            action='admin_resend_invoice_to_owner',
            object_id=self.invoice.pk,
        ).latest('created_at')

        self.assertEqual(
            audit.new_values['telegram_message_id'],
            777,
        )
