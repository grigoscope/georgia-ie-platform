from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import Counterparty, FinancialAccount
from incomes.models import IncomeEntry
from invoices.models import InvoicePayment
from invoices.services import InvoiceService
from taxes.models import TaxPeriod

User = get_user_model()


class InvoicePaymentAPITests(APITestCase):
    """Тесты API оплаты инвойсов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Entrepreneur',
            tin='123456789',
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
            iban='GE00TB0000000000000000',
            default_declaration_category='cashless_20',
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
        )

        self.other_counterparty = Counterparty.objects.create(
            user=self.other_user,
            name='Other Client',
            type='company',
            country='Georgia',
        )

        self.invoice = InvoiceService().create_invoice(
            user=self.user,
            issue_date=date(2026, 8, 1),
            currency=self.gel,
            counterparty=self.counterparty,
            financial_account=self.account,
            items=[
                {
                    'description': 'Development',
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': '310.00',
                }
            ],
        )

        self.other_invoice = InvoiceService().create_invoice(
            user=self.other_user,
            issue_date=date(2026, 8, 1),
            currency=self.gel,
            counterparty=self.other_counterparty,
            financial_account=self.other_account,
            items=[
                {
                    'description': 'Other service',
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': '500.00',
                }
            ],
        )

        self.client.force_authenticate(user=self.user)

    def _payment_url(self):
        return reverse(
            'invoice-create-payment',
            args=[self.invoice.id],
        )

    def _summary_url(self):
        return reverse(
            'invoice-payment-summary',
            args=[self.invoice.id],
        )

    def _payment_payload(
        self,
        *,
        amount='100.00',
        received_at='2026-08-10T12:00:00+04:00',
    ):
        return {
            'received_at': received_at,
            'financial_account': self.account.id,
            'amount': amount,
            'declaration_category': 'cashless_20',
            'tax_period_deadline': '2026-09-15',
            'payment_method': 'bank_transfer',
        }

    def test_payment_summary_before_payments(self):
        response = self.client.get(self._summary_url())

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            Decimal(response.data['total_amount']),
            Decimal('310.00'),
        )

        self.assertEqual(
            Decimal(response.data['paid_amount']),
            Decimal('0.00'),
        )

        self.assertEqual(
            Decimal(response.data['remaining_amount']),
            Decimal('310.00'),
        )

        self.assertFalse(response.data['is_paid'])

        self.assertEqual(
            response.data['status'],
            'created',
        )

    def test_create_partial_payment(self):
        response = self.client.post(
            self._payment_url(),
            self._payment_payload(amount='100.00'),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data['invoice_status'],
            'partially_paid',
        )

        self.assertEqual(
            Decimal(response.data['payment_amount']),
            Decimal('100.00'),
        )

        self.assertEqual(
            Decimal(response.data['paid_amount']),
            Decimal('100.00'),
        )

        self.assertEqual(
            Decimal(response.data['remaining_amount']),
            Decimal('210.00'),
        )

        self.assertFalse(response.data['is_paid'])

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.status,
            'partially_paid',
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            1,
        )

    def test_partial_then_full_payment(self):
        first_response = self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='100.00',
                received_at=('2026-08-10T12:00:00+04:00'),
            ),
            format='json',
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='210.00',
                received_at=('2026-08-20T12:00:00+04:00'),
            ),
            format='json',
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second_response.data['invoice_status'],
            'paid',
        )

        self.assertEqual(
            Decimal(second_response.data['total_amount']),
            Decimal('310.00'),
        )

        self.assertEqual(
            Decimal(second_response.data['paid_amount']),
            Decimal('310.00'),
        )

        self.assertEqual(
            Decimal(second_response.data['remaining_amount']),
            Decimal('0.00'),
        )

        self.assertTrue(second_response.data['is_paid'])

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.status,
            'paid',
        )

        self.assertIsNotNone(self.invoice.paid_at)

        self.assertEqual(
            self.invoice.paid_at.date(),
            date(2026, 8, 20),
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            2,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            2,
        )

    def test_payment_creates_correct_income(self):
        response = self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='100.00',
                received_at=('2026-08-17T15:30:00+04:00'),
            ),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        income = IncomeEntry.objects.get(id=response.data['income_id'])

        self.assertEqual(
            income.invoice,
            self.invoice,
        )

        self.assertEqual(
            income.counterparty,
            self.counterparty,
        )

        self.assertEqual(
            income.financial_account,
            self.account,
        )

        self.assertEqual(
            income.original_currency,
            self.gel,
        )

        self.assertEqual(
            income.original_amount,
            Decimal('100.0000000000'),
        )

        self.assertEqual(
            income.amount_gel,
            Decimal('100.00'),
        )

        self.assertEqual(
            income.exchange_rate_value,
            Decimal('1.0000000000'),
        )

        self.assertEqual(
            income.exchange_rate_unit,
            1,
        )

        self.assertEqual(
            income.declaration_category,
            'cashless_20',
        )

        self.assertEqual(
            income.document_number,
            'INV-1',
        )

        self.assertEqual(
            income.document_date,
            date(2026, 8, 1),
        )

        self.assertEqual(
            income.received_at.date(),
            date(2026, 8, 17),
        )

    def test_payment_updates_tax_period(self):
        self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='100.00',
            ),
            format='json',
        )

        self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='210.00',
                received_at=('2026-08-20T12:00:00+04:00'),
            ),
            format='json',
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            period.field_20,
            Decimal('310.00'),
        )

        self.assertEqual(
            period.field_17,
            Decimal('310.00'),
        )

        self.assertEqual(
            period.field_15,
            Decimal('310.00'),
        )

        self.assertEqual(
            period.field_26,
            Decimal('3.10'),
        )

    def test_payment_summary_after_partial_payment(self):
        self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='100.00',
            ),
            format='json',
        )

        response = self.client.get(self._summary_url())

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['status'],
            'partially_paid',
        )

        self.assertEqual(
            Decimal(response.data['paid_amount']),
            Decimal('100.00'),
        )

        self.assertEqual(
            Decimal(response.data['remaining_amount']),
            Decimal('210.00'),
        )

        self.assertFalse(response.data['is_paid'])

    def test_third_payment_after_full_payment_is_rejected(self):
        first_response = self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='100.00',
            ),
            format='json',
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='210.00',
                received_at=('2026-08-20T12:00:00+04:00'),
            ),
            format='json',
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        third_response = self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='1.00',
                received_at=('2026-08-21T12:00:00+04:00'),
            ),
            format='json',
        )

        self.assertEqual(
            third_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            2,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            2,
        )

    def test_overpayment_is_rejected_without_creating_income(self):
        response = self.client.post(
            self._payment_url(),
            self._payment_payload(
                amount='311.00',
            ),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            0,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            0,
        )

        self.assertEqual(
            TaxPeriod.objects.count(),
            0,
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.status,
            'created',
        )

    def test_foreign_financial_account_is_rejected(self):
        payload = self._payment_payload()

        payload['financial_account'] = self.other_account.id

        response = self.client.post(
            self._payment_url(),
            payload,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            0,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            0,
        )

    def test_other_users_invoice_is_not_accessible(self):
        payment_url = reverse(
            'invoice-create-payment',
            args=[self.other_invoice.id],
        )

        response = self.client.post(
            payment_url,
            self._payment_payload(),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        summary_url = reverse(
            'invoice-payment-summary',
            args=[self.other_invoice.id],
        )

        response = self.client.get(summary_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_category_is_suggested_when_not_provided(self):
        payload = self._payment_payload()

        payload.pop('declaration_category')

        response = self.client.post(
            self._payment_url(),
            payload,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        income = IncomeEntry.objects.get(id=response.data['income_id'])

        self.assertEqual(
            income.declaration_category,
            'cashless_20',
        )
