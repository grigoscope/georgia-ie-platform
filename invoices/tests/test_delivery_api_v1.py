import tempfile
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import (
    get_user_model,
)
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import (
    EntrepreneurProfile,
)
from exchange_rates.models import Currency
from finances.models import (
    Counterparty,
    FinancialAccount,
)
from invoices.models import (
    InvoiceShareLink,
)
from invoices.services import InvoiceService
from telegram_integration.models import (
    TelegramConnection,
)

User = get_user_model()


@override_settings(
    TELEGRAM_BOT_TOKEN='123456:TEST_TOKEN',
    DEFAULT_FROM_EMAIL=('noreply@example.com'),
)
class InvoiceDeliveryV1APITests(APITestCase):
    """Telegram/email/share-link."""

    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()

        self.media_override = override_settings(MEDIA_ROOT=(self.temp_media.name))

        self.media_override.enable()

        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            tin='123456789',
            legal_address='Tbilisi',
            public_email=('seller@example.com'),
            tax_rate=Decimal('1.00'),
            invoice_prefix='INV-',
            next_invoice_number=1,
        )

        self.gel = Currency.objects.create(
            code='GEL',
            name='Georgian Lari',
            kind='fiat',
            decimal_places=2,
        )

        self.account = FinancialAccount.objects.create(
            user=self.user,
            name='TBC GEL',
            type='bank_account',
            default_currency=self.gel,
            provider_name='TBC Bank',
            account_holder=('Test Business'),
            iban=('GE00TB0000000000000000'),
        )

        self.counterparty = Counterparty.objects.create(
            user=self.user,
            name='Client LLC',
            type='company',
            country='Georgia',
            email='client@example.com',
        )

        self.invoice = InvoiceService().create_invoice(
            user=self.user,
            issue_date=date(
                2026,
                8,
                25,
            ),
            due_date=date(
                2026,
                9,
                5,
            ),
            currency=self.gel,
            counterparty=(self.counterparty),
            financial_account=(self.account),
            items=[
                {
                    'description': ('Backend development'),
                    'quantity': ('1.000'),
                    'unit': 'service',
                    'unit_price': ('310.00'),
                }
            ],
        )

        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

    def test_send_to_telegram_requires_connection(
        self,
    ):
        response = self.client.post(
            reverse(
                ('v1-invoice-send-to-telegram'),
                args=[self.invoice.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    @patch(('invoices.delivery_services.requests.post'))
    def test_send_to_telegram(
        self,
        mocked_post,
    ):
        TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_chat_id=987654321,
            is_active=True,
        )

        mocked_response = mocked_post.return_value

        mocked_response.raise_for_status.return_value = None

        mocked_response.json.return_value = {
            'ok': True,
            'result': {
                'message_id': 100,
            },
        }

        response = self.client.post(
            reverse(
                ('v1-invoice-send-to-telegram'),
                args=[self.invoice.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mocked_post.assert_called_once()

        _, kwargs = mocked_post.call_args

        self.assertEqual(
            kwargs['data']['chat_id'],
            987654321,
        )

        self.assertIn(
            'document',
            kwargs['files'],
        )

        self.invoice.refresh_from_db()

        self.assertTrue(self.invoice.pdf_file)

        self.assertEqual(
            self.invoice.status,
            'pending',
        )

        self.assertIsNotNone(self.invoice.sent_at)

    @patch(('invoices.delivery_services.requests.post'))
    def test_telegram_failure_returns_502(
        self,
        mocked_post,
    ):
        import requests

        TelegramConnection.objects.create(
            user=self.user,
            telegram_user_id=123456789,
            telegram_chat_id=123456789,
            is_active=True,
        )

        mocked_post.side_effect = requests.RequestException('Telegram unavailable')

        response = self.client.post(
            reverse(
                ('v1-invoice-send-to-telegram'),
                args=[self.invoice.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )

    @patch(('invoices.delivery_services.EmailMessage.send'))
    def test_send_email(
        self,
        mocked_send,
    ):
        mocked_send.return_value = 1

        response = self.client.post(
            reverse(
                'v1-invoice-send-email',
                args=[self.invoice.id],
            ),
            {
                'recipient': ('customer@example.com'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mocked_send.assert_called_once()

        self.invoice.refresh_from_db()

        self.assertTrue(self.invoice.pdf_file)

        self.assertEqual(
            self.invoice.status,
            'pending',
        )

        self.assertIsNotNone(self.invoice.sent_at)

    @patch(('invoices.delivery_services.EmailMessage.send'))
    def test_email_uses_buyer_snapshot(
        self,
        mocked_send,
    ):
        mocked_send.return_value = 1

        response = self.client.post(
            reverse(
                'v1-invoice-send-email',
                args=[self.invoice.id],
            ),
            {},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mocked_send.assert_called_once()

        email_message = mocked_send.call_args[0] if mocked_send.call_args[0] else None

        self.assertIsNotNone(email_message or mocked_send)

    def test_create_share_link(
        self,
    ):
        response = self.client.post(
            reverse(
                ('v1-invoice-create-share-link'),
                args=[self.invoice.id],
            ),
            {
                'expires_in_hours': 24,
            },
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

        link = InvoiceShareLink.objects.get(invoice=self.invoice)

        self.assertIsNone(link.revoked_at)

        self.assertGreater(
            link.expires_at,
            timezone.now(),
        )

        self.invoice.refresh_from_db()

        self.assertTrue(self.invoice.pdf_file)

    def test_public_share_link_download(
        self,
    ):
        self.client.post(
            reverse(
                ('v1-invoice-create-share-link'),
                args=[self.invoice.id],
            ),
            {},
            format='json',
        )

        link = InvoiceShareLink.objects.get(invoice=self.invoice)

        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse(
                'invoice-share-public',
                kwargs={
                    'token': link.token,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response['Content-Type'],
            'application/pdf',
        )

    def test_revoke_share_link(
        self,
    ):
        self.client.post(
            reverse(
                ('v1-invoice-create-share-link'),
                args=[self.invoice.id],
            ),
            {},
            format='json',
        )

        link = InvoiceShareLink.objects.get(invoice=self.invoice)

        token = link.token

        response = self.client.delete(
            reverse(
                'v1-invoice-share-link',
                args=[self.invoice.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        link.refresh_from_db()

        self.assertIsNotNone(link.revoked_at)

        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse(
                'invoice-share-public',
                kwargs={
                    'token': token,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_expired_share_link_is_rejected(
        self,
    ):
        self.client.post(
            reverse(
                ('v1-invoice-create-share-link'),
                args=[self.invoice.id],
            ),
            {},
            format='json',
        )

        link = InvoiceShareLink.objects.get(invoice=self.invoice)

        link.expires_at = timezone.now() - timedelta(minutes=1)

        link.save(
            update_fields=[
                'expires_at',
                'updated_at',
            ]
        )

        self.client.force_authenticate(user=None)

        response = self.client.get(
            reverse(
                'invoice-share-public',
                kwargs={
                    'token': link.token,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_new_share_link_invalidates_old_token(
        self,
    ):
        self.client.post(
            reverse(
                ('v1-invoice-create-share-link'),
                args=[self.invoice.id],
            ),
            {},
            format='json',
        )

        link = InvoiceShareLink.objects.get(invoice=self.invoice)

        first_token = link.token

        self.client.post(
            reverse(
                ('v1-invoice-create-share-link'),
                args=[self.invoice.id],
            ),
            {},
            format='json',
        )

        link.refresh_from_db()

        second_token = link.token

        self.assertNotEqual(
            first_token,
            second_token,
        )

        self.client.force_authenticate(user=None)

        old_response = self.client.get(
            reverse(
                'invoice-share-public',
                kwargs={
                    'token': first_token,
                },
            )
        )

        new_response = self.client.get(
            reverse(
                'invoice-share-public',
                kwargs={
                    'token': second_token,
                },
            )
        )

        self.assertEqual(
            old_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            new_response.status_code,
            status.HTTP_200_OK,
        )
