import tempfile
from decimal import Decimal

from django.contrib.auth import (
    get_user_model,
)
from django.test import override_settings
from django.urls import reverse
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
from invoices.models import Invoice

User = get_user_model()


class InvoiceV1APITests(APITestCase):
    """Stage 4 API инвойсов."""

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
            tax_rate=Decimal('1.00'),
            invoice_prefix='INV-',
            next_invoice_number=1,
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='StrongPass123!',
        )

        EntrepreneurProfile.objects.create(
            user=self.other_user,
            business_name='Other',
            tin='987654321',
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
        )

        self.counterparty = Counterparty.objects.create(
            user=self.user,
            name='Client LLC',
            type='company',
            country='Georgia',
        )

        self.client.force_authenticate(user=self.user)

        self.list_url = reverse('v1-invoice-list')

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

    def _payload(self):
        return {
            'issue_date': '2026-08-25',
            'due_date': '2026-09-05',
            'currency': self.gel.id,
            'language': 'en',
            'counterparty': (self.counterparty.id),
            'financial_account': (self.account.id),
            'items': [
                {
                    'description': ('Backend development'),
                    'quantity': '1.000',
                    'unit': 'service',
                    'unit_price': '310.00',
                }
            ],
        }

    def _create(self):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        return response.data['id']

    def test_requires_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_create_and_list_are_paginated(
        self,
    ):
        self._create()

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
            response.data['results'][0]['total_amount'],
            '310.00',
        )

    def test_foreign_invoice_is_hidden(
        self,
    ):
        other_account = FinancialAccount.objects.create(
            user=self.other_user,
            name='Other',
            type='bank_account',
            default_currency=self.gel,
        )

        other_counterparty = Counterparty.objects.create(
            user=self.other_user,
            name='Other Client',
            type='company',
        )

        from invoices.services import (
            InvoiceService,
        )

        invoice = InvoiceService().create_invoice(
            user=self.other_user,
            issue_date=(
                __import__('datetime').date(
                    2026,
                    8,
                    25,
                )
            ),
            currency=self.gel,
            counterparty=(other_counterparty),
            financial_account=(other_account),
            items=[
                {
                    'description': ('Other'),
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': ('100.00'),
                }
            ],
        )

        response = self.client.get(
            reverse(
                'v1-invoice-detail',
                args=[invoice.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_preview(self):
        invoice_id = self._create()

        response = self.client.post(
            reverse(
                'v1-invoice-preview',
                args=[invoice_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['data']['invoice']['total_amount'],
            '310.00',
        )

        self.assertEqual(
            response.data['data']['payment_summary']['remaining_amount'],
            '310.00',
        )

    def test_generate_and_download_pdf(
        self,
    ):
        invoice_id = self._create()

        response = self.client.post(
            reverse(
                ('v1-invoice-generate-pdf'),
                args=[invoice_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        invoice = Invoice.objects.get(id=invoice_id)

        self.assertTrue(invoice.pdf_file)

        response = self.client.get(
            reverse(
                'v1-invoice-pdf',
                args=[invoice_id],
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

    def test_duplicate(self):
        invoice_id = self._create()

        response = self.client.post(
            reverse(
                'v1-invoice-duplicate',
                args=[invoice_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Invoice.objects.filter(user=self.user).count(),
            2,
        )

        self.assertNotEqual(
            response.data['number'],
            'INV-1',
        )

        self.assertEqual(
            response.data['total_amount'],
            '310.00',
        )

    def test_mark_sent(self):
        invoice_id = self._create()

        response = self.client.post(
            reverse(
                'v1-invoice-mark-sent',
                args=[invoice_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        invoice = Invoice.objects.get(id=invoice_id)

        self.assertEqual(
            invoice.status,
            'pending',
        )

        self.assertIsNotNone(invoice.sent_at)

    def test_cancel(self):
        invoice_id = self._create()

        response = self.client.post(
            reverse(
                'v1-invoice-cancel',
                args=[invoice_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        invoice = Invoice.objects.get(id=invoice_id)

        self.assertEqual(
            invoice.status,
            'cancelled',
        )

        self.assertIsNotNone(invoice.cancelled_at)

    def test_delete_draft(self):
        invoice_id = self._create()

        response = self.client.delete(
            reverse(
                'v1-invoice-detail',
                args=[invoice_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(Invoice.objects.filter(id=invoice_id).exists())

    def test_non_draft_cannot_be_deleted(
        self,
    ):
        invoice_id = self._create()

        self.client.post(
            reverse(
                'v1-invoice-mark-sent',
                args=[invoice_id],
            )
        )

        response = self.client.delete(
            reverse(
                'v1-invoice-detail',
                args=[invoice_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_filters(self):
        self._create()

        response = self.client.get(
            self.list_url,
            {
                'status': 'draft',
                'currency': 'GEL',
                'counterparty': (self.counterparty.id),
                'search': 'INV-',
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
