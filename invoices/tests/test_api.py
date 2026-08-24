import tempfile
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import Counterparty, FinancialAccount
from invoices.models import Invoice
from invoices.services import InvoiceService

User = get_user_model()


class InvoiceAPITests(APITestCase):
    """Тесты API инвойсов."""

    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()

        self.media_override = override_settings(
            MEDIA_ROOT=self.temp_media.name,
        )
        self.media_override.enable()

        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Entrepreneur',
            tin='123456789',
            legal_address='Tbilisi',
            tax_rate=Decimal('1.00'),
            invoice_prefix='INV-',
            next_invoice_number=1,
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.other_user,
            business_name='Other Entrepreneur',
            tin='987654321',
            legal_address='Batumi',
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
            account_holder='Test Entrepreneur',
            iban='GE00TB0000000000000000',
            swift_bic='TBCBGE22',
        )

        self.other_account = FinancialAccount.objects.create(
            user=self.other_user,
            name='Other Account',
            type='bank_account',
            default_currency=self.gel,
        )

        self.counterparty = Counterparty.objects.create(
            user=self.user,
            name='Client LLC',
            type='company',
            country='Georgia',
            tax_id='111222333',
            address='Tbilisi',
            email='client@example.com',
        )

        self.other_counterparty = Counterparty.objects.create(
            user=self.other_user,
            name='Other Client',
            type='company',
            country='Georgia',
        )

        self.client.force_authenticate(user=self.user)

        self.list_url = reverse('invoice-list')

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

    def _payload(self):
        return {
            'issue_date': '2026-08-22',
            'due_date': '2026-09-05',
            'currency': self.gel.id,
            'language': 'en',
            'counterparty': self.counterparty.id,
            'financial_account': self.account.id,
            'items': [
                {
                    'description': 'Backend development',
                    'quantity': '2.000',
                    'unit': 'hour',
                    'unit_price': '100.00',
                },
                {
                    'description': 'Consulting',
                    'quantity': '1.000',
                    'unit': 'service',
                    'unit_price': '110.00',
                },
            ],
            'discount_amount': '0.00',
            'extra_charge_amount': '0.00',
            'payment_purpose': 'Payment for invoice',
        }

    def _create_other_invoice(self):
        return InvoiceService().create_invoice(
            user=self.other_user,
            issue_date=date(2026, 8, 22),
            currency=self.gel,
            counterparty=self.other_counterparty,
            financial_account=self.other_account,
            items=[
                {
                    'description': 'Other service',
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': '100.00',
                }
            ],
        )

    def test_create_invoice(self):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Invoice.objects.count(),
            1,
        )

        invoice = Invoice.objects.get()

        self.assertEqual(
            invoice.user,
            self.user,
        )

        self.assertEqual(
            invoice.number,
            'INV-1',
        )

        self.assertEqual(
            invoice.subtotal,
            Decimal('310.00'),
        )

        self.assertEqual(
            invoice.total_amount,
            Decimal('310.00'),
        )

        self.assertEqual(
            invoice.invoice_items.count(),
            2,
        )

        self.assertEqual(
            invoice.status,
            'draft',
        )

    def test_create_invoice_with_discount_and_extra_charge(self):
        payload = self._payload()

        payload['discount_amount'] = '20.00'
        payload['extra_charge_amount'] = '10.00'

        response = self.client.post(
            self.list_url,
            payload,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        invoice = Invoice.objects.get()

        self.assertEqual(
            invoice.subtotal,
            Decimal('310.00'),
        )

        self.assertEqual(
            invoice.discount_amount,
            Decimal('20.00'),
        )

        self.assertEqual(
            invoice.extra_charge_amount,
            Decimal('10.00'),
        )

        self.assertEqual(
            invoice.total_amount,
            Decimal('300.00'),
        )

    def test_list_contains_only_current_user_invoices(self):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self._create_other_invoice()

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.data

        if isinstance(data, dict):
            data = data.get('results', [])

        self.assertEqual(
            len(data),
            1,
        )

        self.assertEqual(
            data[0]['number'],
            'INV-1',
        )

    def test_user_cannot_access_other_invoice(self):
        other_invoice = self._create_other_invoice()

        url = reverse(
            'invoice-detail',
            args=[other_invoice.id],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_foreign_counterparty_is_rejected(self):
        payload = self._payload()

        payload['counterparty'] = self.other_counterparty.id

        response = self.client.post(
            self.list_url,
            payload,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Invoice.objects.count(),
            0,
        )

    def test_foreign_financial_account_is_rejected(self):
        payload = self._payload()

        payload['financial_account'] = self.other_account.id

        response = self.client.post(
            self.list_url,
            payload,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Invoice.objects.count(),
            0,
        )

    def test_generate_pdf(self):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        invoice_id = response.data['id']

        url = reverse(
            'invoice-generate-pdf',
            args=[invoice_id],
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        invoice = Invoice.objects.get(id=invoice_id)

        self.assertTrue(invoice.pdf_file)

        self.assertEqual(
            len(invoice.pdf_checksum),
            64,
        )

        self.assertIsNotNone(invoice.generated_at)

    def test_download_pdf(self):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        invoice_id = response.data['id']

        generate_url = reverse(
            'invoice-generate-pdf',
            args=[invoice_id],
        )

        self.client.post(generate_url)

        download_url = reverse(
            'invoice-download-pdf',
            args=[invoice_id],
        )

        response = self.client.get(download_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response['Content-Type'],
            'application/pdf',
        )

        pdf_bytes = b''.join(response.streaming_content)

        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

        self.assertGreater(
            len(pdf_bytes),
            1000,
        )

    def test_download_without_pdf_returns_404(self):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        invoice_id = response.data['id']

        download_url = reverse(
            'invoice-download-pdf',
            args=[invoice_id],
        )

        response = self.client.get(download_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_patch_draft_invoice(self):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        invoice_id = response.data['id']

        url = reverse(
            'invoice-detail',
            args=[invoice_id],
        )

        response = self.client.patch(
            url,
            {
                'notes': ('Updated draft notes'),
                'discount_amount': ('10.00'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        invoice = Invoice.objects.get(id=invoice_id)

        self.assertEqual(
            invoice.status,
            'draft',
        )

        self.assertEqual(
            invoice.notes,
            'Updated draft notes',
        )

        self.assertEqual(
            invoice.subtotal,
            Decimal('310.00'),
        )

        self.assertEqual(
            invoice.discount_amount,
            Decimal('10.00'),
        )

        self.assertEqual(
            invoice.total_amount,
            Decimal('300.00'),
        )

    def test_patch_draft_items_recalculates_total(
        self,
    ):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        invoice_id = response.data['id']

        url = reverse(
            'invoice-detail',
            args=[invoice_id],
        )

        response = self.client.patch(
            url,
            {
                'items': [
                    {
                        'description': ('New service'),
                        'quantity': '2.000',
                        'unit': 'service',
                        'unit_price': ('250.00'),
                    }
                ],
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        invoice = Invoice.objects.get(id=invoice_id)

        self.assertEqual(
            invoice.invoice_items.count(),
            1,
        )

        self.assertEqual(
            invoice.subtotal,
            Decimal('500.00'),
        )

        self.assertEqual(
            invoice.total_amount,
            Decimal('500.00'),
        )

    def test_non_draft_invoice_cannot_be_patched(
        self,
    ):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        invoice_id = response.data['id']

        invoice = Invoice.objects.get(id=invoice_id)

        invoice.status = 'pending'

        invoice.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )

        url = reverse(
            'invoice-detail',
            args=[invoice_id],
        )

        response = self.client.patch(
            url,
            {
                'notes': ('Should not change'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invoice.refresh_from_db()

        self.assertNotEqual(
            invoice.notes,
            'Should not change',
        )

    def test_delete_is_not_allowed(self):
        response = self.client.post(
            self.list_url,
            self._payload(),
            format='json',
        )

        invoice_id = response.data['id']

        url = reverse(
            'invoice-detail',
            args=[invoice_id],
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

        self.assertTrue(Invoice.objects.filter(id=invoice_id).exists())
