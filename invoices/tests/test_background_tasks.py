from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from exchange_rates.models import Currency
from finances.models import Counterparty
from invoices.models import (
    Invoice,
    InvoiceShareLink,
)
from invoices.tasks import (
    cleanup_expired_share_links,
    generate_invoice_pdf,
    mark_overdue_invoices,
    send_invoice_pdf_telegram,
)
from telegram_integration.models import (
    TelegramConnection,
)


class InvoiceBackgroundTasksTests(
    TestCase,
):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                email='invoice-tasks@example.com',
                password='Password123!',
            )
        )

        self.currency = (
            Currency.objects.create(
                code='GEL',
                name='Georgian Lari',
                kind='fiat',
                is_active=True,
            )
        )

        self.counterparty = (
            Counterparty.objects.create(
                user=self.user,
                name='Test Buyer',
                type='company',
            )
        )

        self.invoice = (
            Invoice.objects.create(
                user=self.user,
                number='INV-TASK-1',
                issue_date=date(
                    2026,
                    9,
                    1,
                ),
                due_date=date(
                    2026,
                    9,
                    10,
                ),
                currency=self.currency,
                language='en',
                status='pending',
                counterparty=self.counterparty,
                seller_snapshot={},
                buyer_snapshot={},
                payment_details_snapshot={},
            )
        )

    @patch(
        'invoices.tasks.'
        'InvoicePDFService.generate'
    )
    def test_generate_invoice_pdf_task(
        self,
        generate,
    ):
        result = generate_invoice_pdf(
            self.invoice.pk,
        )

        self.assertEqual(
            result['status'],
            'generated',
        )

        generate.assert_called_once()

    def test_cleanup_expired_share_links(
        self,
    ):
        expired = (
            InvoiceShareLink.objects
            .create(
                invoice=self.invoice,
                expires_at=(
                    timezone.now()
                    - timedelta(hours=1)
                ),
            )
        )

        result = (
            cleanup_expired_share_links()
        )

        self.assertGreaterEqual(
            result['deleted'],
            1,
        )

        self.assertFalse(
            InvoiceShareLink.objects
            .filter(pk=expired.pk)
            .exists()
        )

    @patch(
        'invoices.tasks.timezone.localdate'
    )
    def test_mark_overdue_invoices(
        self,
        localdate,
    ):
        localdate.return_value = date(
            2026,
            9,
            14,
        )

        result = (
            mark_overdue_invoices()
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            result['marked_overdue'],
            1,
        )

        self.assertTrue(
            self.invoice.is_overdue,
        )

    @patch(
        'invoices.tasks.'
        'InvoiceDeliveryService.send_to_telegram'
    )
    def test_send_pdf_to_telegram(
        self,
        send_to_telegram,
    ):
        TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=100,
            telegram_chat_id=200,
            is_active=True,
        )

        send_to_telegram.return_value = {
            'ok': True,
            'result': {
                'message_id': 777,
            },
        }

        result = (
            send_invoice_pdf_telegram(
                self.invoice.pk,
            )
        )

        self.assertEqual(
            result['status'],
            'sent',
        )

        self.assertEqual(
            result['message_id'],
            777,
        )

    def test_duplicate_telegram_send_is_skipped(
        self,
    ):
        self.invoice.telegram_sent_at = (
            timezone.now()
        )

        self.invoice.telegram_message_id = (
            555
        )

        self.invoice.save(
            update_fields=[
                'telegram_sent_at',
                'telegram_message_id',
                'updated_at',
            ],
        )

        result = (
            send_invoice_pdf_telegram(
                self.invoice.pk,
            )
        )

        self.assertEqual(
            result['status'],
            'already_sent',
        )

        self.assertEqual(
            result['message_id'],
            555,
        )
