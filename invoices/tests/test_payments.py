from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import Counterparty, FinancialAccount
from incomes.models import IncomeEntry
from invoices.models import InvoicePayment
from invoices.payment_services import InvoicePaymentService
from invoices.services import InvoiceService
from taxes.models import TaxPeriod

User = get_user_model()


class InvoicePaymentServiceTests(TestCase):
    """Тесты оплат инвойсов."""

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

        self.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
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
        )

        self.other_account = FinancialAccount.objects.create(
            user=self.other_user,
            name='Other account',
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

        self.service = InvoicePaymentService()

        self.deadline = date(
            2026,
            9,
            15,
        )

    def _received_at(
        self,
        day,
    ):
        return timezone.make_aware(
            datetime(
                2026,
                8,
                day,
                12,
                0,
            )
        )

    def _create_payment(
        self,
        *,
        amount,
        day,
    ):
        return self.service.create_income_from_invoice(
            invoice=self.invoice,
            received_at=self._received_at(day),
            financial_account=self.account,
            amount=Decimal(str(amount)),
            declaration_category='cashless_20',
            tax_period_deadline=self.deadline,
            payment_method='bank_transfer',
        )

    def test_partial_payment(self):
        result = self._create_payment(
            amount='100.00',
            day=10,
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.status,
            'partially_paid',
        )

        self.assertIsNone(self.invoice.paid_at)

        self.assertEqual(
            result['summary']['total_amount'],
            Decimal('310.00'),
        )

        self.assertEqual(
            result['summary']['paid_amount'],
            Decimal('100.00'),
        )

        self.assertEqual(
            result['summary']['remaining_amount'],
            Decimal('210.00'),
        )

        self.assertFalse(result['summary']['is_paid'])

    def test_partial_payment_creates_income_and_payment(self):
        result = self._create_payment(
            amount='100.00',
            day=10,
        )

        income = result['income']
        payment = result['payment']

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            1,
        )

        self.assertEqual(
            income.invoice,
            self.invoice,
        )

        self.assertEqual(
            income.counterparty,
            self.counterparty,
        )

        self.assertEqual(
            income.original_amount,
            Decimal('100.00'),
        )

        self.assertEqual(
            income.amount_gel,
            Decimal('100.00'),
        )

        self.assertEqual(
            income.declaration_category,
            'cashless_20',
        )

        self.assertEqual(
            payment.invoice,
            self.invoice,
        )

        self.assertEqual(
            payment.income_entry,
            income,
        )

        self.assertEqual(
            payment.amount,
            Decimal('100.00'),
        )

        self.assertEqual(
            payment.currency,
            self.gel,
        )

    def test_payment_uses_actual_income_date_not_invoice_date(self):
        result = self._create_payment(
            amount='100.00',
            day=21,
        )

        income = result['income']

        self.assertEqual(
            income.received_at.date(),
            date(2026, 8, 21),
        )

        self.assertEqual(
            self.invoice.issue_date,
            date(2026, 8, 1),
        )

        self.assertNotEqual(
            income.received_at.date(),
            self.invoice.issue_date,
        )

    def test_full_payment_after_partial_payment(self):
        self._create_payment(
            amount='100.00',
            day=10,
        )

        result = self._create_payment(
            amount='210.00',
            day=20,
        )

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
            result['summary']['paid_amount'],
            Decimal('310.00'),
        )

        self.assertEqual(
            result['summary']['remaining_amount'],
            Decimal('0.00'),
        )

        self.assertTrue(result['summary']['is_paid'])

        self.assertEqual(
            InvoicePayment.objects.count(),
            2,
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            2,
        )

    def test_payments_update_tax_period(self):
        self._create_payment(
            amount='100.00',
            day=10,
        )

        self._create_payment(
            amount='210.00',
            day=20,
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

    def test_overpayment_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._create_payment(
                amount='311.00',
                day=10,
            )

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.status,
            'draft',
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

    def test_payment_after_full_payment_is_rejected(self):
        self._create_payment(
            amount='310.00',
            day=10,
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.status,
            'paid',
        )

        with self.assertRaises(ValidationError):
            self._create_payment(
                amount='1.00',
                day=20,
            )

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            1,
        )

    def test_same_income_cannot_be_registered_twice(self):
        result = self._create_payment(
            amount='100.00',
            day=10,
        )

        income = result['income']

        with self.assertRaises(ValidationError):
            self.service.register_income_payment(
                invoice=self.invoice,
                income_entry=income,
            )

        self.assertEqual(
            InvoicePayment.objects.count(),
            1,
        )

    def test_foreign_income_is_rejected(self):
        foreign_income = IncomeEntry.objects.create(
            user=self.other_user,
            received_at=self._received_at(10),
            description='Foreign income',
            financial_account=self.other_account,
            original_amount=Decimal('100.00'),
            original_currency=self.gel,
            exchange_rate_value=Decimal('1'),
            exchange_rate_unit=1,
            exchange_rate_source='GEL',
            exchange_rate_date=date(2026, 8, 10),
            amount_gel=Decimal('100.00'),
            declaration_category='cashless_20',
        )

        with self.assertRaises(ValidationError):
            self.service.register_income_payment(
                invoice=self.invoice,
                income_entry=foreign_income,
            )

        self.assertEqual(
            InvoicePayment.objects.count(),
            0,
        )

    def test_income_with_different_currency_is_rejected(self):
        usd_account = FinancialAccount.objects.create(
            user=self.user,
            name='TBC USD',
            type='bank_account',
            default_currency=self.usd,
        )

        income = IncomeEntry.objects.create(
            user=self.user,
            received_at=self._received_at(10),
            description='USD income',
            financial_account=usd_account,
            original_amount=Decimal('100.00'),
            original_currency=self.usd,
            exchange_rate_value=Decimal('2.70'),
            exchange_rate_unit=1,
            exchange_rate_source='manual',
            exchange_rate_date=date(2026, 8, 10),
            amount_gel=Decimal('270.00'),
            declaration_category='cashless_20',
        )

        with self.assertRaises(ValidationError):
            self.service.register_income_payment(
                invoice=self.invoice,
                income_entry=income,
            )

        self.assertEqual(
            InvoicePayment.objects.count(),
            0,
        )

    def test_cancelled_invoice_cannot_be_paid(self):
        self.invoice.status = 'cancelled'
        self.invoice.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )

        with self.assertRaises(ValidationError):
            self._create_payment(
                amount='100.00',
                day=10,
            )

        self.assertEqual(
            IncomeEntry.objects.count(),
            0,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            0,
        )
