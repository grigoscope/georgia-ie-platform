import tempfile
from datetime import date
from decimal import Decimal
from unittest.mock import patch

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
from incomes.models import IncomeEntry
from invoices.models import (
    InvoicePayment,
)
from invoices.services import InvoiceService

User = get_user_model()


class IdempotencyAPITests(APITestCase):
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
            account_holder='Test Business',
        )

        self.counterparty = Counterparty.objects.create(
            user=self.user,
            name='Client LLC',
            type='company',
            country='Georgia',
        )

        self.client.force_authenticate(user=self.user)

        self.income_url = reverse('v1-income-list')

        self.invoice = InvoiceService().create_invoice(
            user=self.user,
            issue_date=date(
                2026,
                8,
                29,
            ),
            currency=self.gel,
            counterparty=(self.counterparty),
            financial_account=(self.account),
            items=[
                {
                    'description': ('Backend development'),
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': ('310.00'),
                }
            ],
        )

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

    def _income_payload(
        self,
        amount='100.00',
    ):
        return {
            'received_at': ('2026-08-29T12:00:00+04:00'),
            'description': 'Consulting',
            'financial_account': (self.account.id),
            'original_amount': amount,
            'original_currency': (self.gel.id),
            'declaration_category': ('cashless_20'),
        }

    def test_income_create_is_idempotent(
        self,
    ):
        payload = self._income_payload()

        first = self.client.post(
            self.income_url,
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY=('income-create-1'),
        )

        second = self.client.post(
            self.income_url,
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY=('income-create-1'),
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

        self.assertEqual(
            first.data['id'],
            second.data['id'],
        )

        self.assertEqual(
            second['Idempotent-Replayed'],
            'true',
        )

    def test_same_key_with_different_body_returns_409(
        self,
    ):
        first = self.client.post(
            self.income_url,
            self._income_payload('100.00'),
            format='json',
            HTTP_IDEMPOTENCY_KEY=('income-conflict-1'),
        )

        second = self.client.post(
            self.income_url,
            self._income_payload('200.00'),
            format='json',
            HTTP_IDEMPOTENCY_KEY=('income-conflict-1'),
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_409_CONFLICT,
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

    def test_invoice_payment_is_idempotent(
        self,
    ):
        url = reverse(
            'v1-invoice-create-income',
            args=[self.invoice.id],
        )

        payload = {
            'received_at': ('2026-08-29T13:00:00+04:00'),
            'financial_account': (self.account.id),
            'amount': '100.00',
            'declaration_category': ('cashless_20'),
        }

        first = self.client.post(
            url,
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY=('invoice-payment-1'),
        )

        second = self.client.post(
            url,
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY=('invoice-payment-1'),
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            1,
        )

        self.assertEqual(
            first.data['data']['income_id'],
            second.data['data']['income_id'],
        )

        self.assertEqual(
            second['Idempotent-Replayed'],
            'true',
        )

    @patch(('invoices.views.InvoicePDFService.generate'))
    def test_pdf_generation_is_idempotent(
        self,
        mocked_generate,
    ):
        mocked_generate.side_effect = lambda invoice: invoice

        url = reverse(
            'v1-invoice-generate-pdf',
            args=[self.invoice.id],
        )

        first = self.client.post(
            url,
            {},
            format='json',
            HTTP_IDEMPOTENCY_KEY=('invoice-pdf-1'),
        )

        second = self.client.post(
            url,
            {},
            format='json',
            HTTP_IDEMPOTENCY_KEY=('invoice-pdf-1'),
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            mocked_generate.call_count,
            1,
        )

        self.assertEqual(
            second['Idempotent-Replayed'],
            'true',
        )

    def test_mark_paid_is_idempotent(
        self,
    ):
        url = reverse(
            'v1-invoice-mark-paid',
            args=[self.invoice.id],
        )

        first = self.client.post(
            url,
            {},
            format='json',
            HTTP_IDEMPOTENCY_KEY=('invoice-paid-1'),
        )

        self.invoice.refresh_from_db()

        first_paid_at = self.invoice.paid_at

        second = self.client.post(
            url,
            {},
            format='json',
            HTTP_IDEMPOTENCY_KEY=('invoice-paid-1'),
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            first.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            self.invoice.paid_at,
            first_paid_at,
        )

        self.assertEqual(
            second['Idempotent-Replayed'],
            'true',
        )
