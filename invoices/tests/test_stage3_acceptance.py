import tempfile
from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import Counterparty, FinancialAccount
from incomes.models import IncomeEntry
from incomes.reports import IncomeReportService
from incomes.services import IncomeService
from invoices.models import InvoicePayment
from invoices.payment_services import InvoicePaymentService
from invoices.pdf import InvoicePDFService
from invoices.services import InvoiceService
from taxes.models import TaxPeriod

User = get_user_model()


class Stage3AcceptanceTests(TestCase):
    """Сквозной acceptance-тест этапа 3."""

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
            legal_address='Tbilisi, Georgia',
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

        self.usd_account = FinancialAccount.objects.create(
            user=self.user,
            name='TBC USD',
            type='bank_account',
            default_currency=self.usd,
            provider_name='TBC Bank',
            iban='GE00TB0000000000000001',
            default_declaration_category='cashless_20',
        )

        self.gel_account = FinancialAccount.objects.create(
            user=self.user,
            name='TBC GEL',
            type='bank_account',
            default_currency=self.gel,
            provider_name='TBC Bank',
            iban='GE00TB0000000000000002',
            default_declaration_category='cashless_20',
            use_in_invoices=True,
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

        self.tax_deadline = date(
            2026,
            9,
            15,
        )

        self.income_service = IncomeService()
        self.report_service = IncomeReportService()
        self.invoice_service = InvoiceService()
        self.pdf_service = InvoicePDFService()
        self.payment_service = InvoicePaymentService()

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

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

    def test_stage3_full_acceptance_scenario(self):

        first_income = self.income_service.create_income(
            user=self.user,
            received_at=self._received_at(5),
            description='Backend development',
            counterparty=self.counterparty,
            financial_account=self.usd_account,
            payment_method='bank_transfer',
            original_amount=Decimal('500.00'),
            original_currency=self.usd,
            declaration_category='cashless_20',
            manual_rate_value=Decimal('2.70'),
            manual_rate_unit=1,
            manual_source='manual_acceptance_test',
            tax_period_deadline=(self.tax_deadline),
        )

        self.assertEqual(
            first_income.original_amount,
            Decimal('500.0000000000'),
        )

        self.assertEqual(
            first_income.original_currency,
            self.usd,
        )

        self.assertEqual(
            first_income.exchange_rate_value,
            Decimal('2.7000000000'),
        )

        self.assertEqual(
            first_income.exchange_rate_unit,
            1,
        )

        self.assertEqual(
            first_income.exchange_rate_source,
            'manual_acceptance_test',
        )

        self.assertEqual(
            first_income.amount_gel,
            Decimal('1350.00'),
        )

        self.assertEqual(
            first_income.declaration_category,
            'cashless_20',
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            period.field_18,
            Decimal('0.00'),
        )

        self.assertEqual(
            period.field_19,
            Decimal('0.00'),
        )

        self.assertEqual(
            period.field_20,
            Decimal('1350.00'),
        )

        self.assertEqual(
            period.field_21,
            Decimal('0.00'),
        )

        self.assertEqual(
            period.field_17,
            Decimal('1350.00'),
        )

        self.assertEqual(
            period.field_15,
            Decimal('1350.00'),
        )

        self.assertEqual(
            period.field_26,
            Decimal('13.50'),
        )

        report = self.report_service.monthly(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            report['total_gel'],
            Decimal('1350.00'),
        )

        self.assertEqual(
            report['count'],
            1,
        )

        self.assertEqual(
            report['categories']['cashless_20']['total_gel'],
            Decimal('1350.00'),
        )

        self.assertEqual(
            report['categories']['cashless_20']['count'],
            1,
        )

        self.assertTrue(report['matches_tax_period'])

        invoice = self.invoice_service.create_invoice(
            user=self.user,
            issue_date=date(2026, 8, 10),
            due_date=date(2026, 8, 25),
            currency=self.gel,
            counterparty=self.counterparty,
            financial_account=self.gel_account,
            items=[
                {
                    'description': ('Backend development'),
                    'quantity': '2',
                    'unit': 'hour',
                    'unit_price': '100.00',
                },
                {
                    'description': ('Consulting'),
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': '110.00',
                },
            ],
            language='en',
            payment_purpose=('Payment for invoice'),
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

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

        self.pdf_service.generate(invoice=invoice)

        invoice.refresh_from_db()

        self.assertTrue(invoice.pdf_file)

        self.assertEqual(
            len(invoice.pdf_checksum),
            64,
        )

        self.assertIsNotNone(invoice.generated_at)

        with invoice.pdf_file.open('rb') as file:
            pdf_bytes = file.read()

        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

        self.assertGreater(
            len(pdf_bytes),
            1000,
        )

        payment_result = self.payment_service.create_income_from_invoice(
            invoice=invoice,
            received_at=self._received_at(20),
            financial_account=self.gel_account,
            amount=Decimal('310.00'),
            declaration_category='cashless_20',
            tax_period_deadline=(self.tax_deadline),
            payment_method='bank_transfer',
        )

        invoice.refresh_from_db()

        second_income = payment_result['income']

        payment = payment_result['payment']

        summary = payment_result['summary']

        self.assertEqual(
            invoice.status,
            'paid',
        )

        self.assertIsNotNone(invoice.paid_at)

        self.assertEqual(
            invoice.paid_at.date(),
            date(2026, 8, 20),
        )

        self.assertEqual(
            second_income.invoice,
            invoice,
        )

        self.assertEqual(
            second_income.original_amount,
            Decimal('310.0000000000'),
        )

        self.assertEqual(
            second_income.amount_gel,
            Decimal('310.00'),
        )

        self.assertEqual(
            second_income.received_at.date(),
            date(2026, 8, 20),
        )

        self.assertEqual(
            second_income.document_number,
            'INV-1',
        )

        self.assertEqual(
            payment.amount,
            Decimal('310.00'),
        )

        self.assertEqual(
            payment.currency,
            self.gel,
        )

        self.assertEqual(
            summary['total_amount'],
            Decimal('310.00'),
        )

        self.assertEqual(
            summary['paid_amount'],
            Decimal('310.00'),
        )

        self.assertEqual(
            summary['remaining_amount'],
            Decimal('0.00'),
        )

        self.assertTrue(summary['is_paid'])

        self.assertEqual(
            IncomeEntry.objects.count(),
            2,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            1,
        )

        period.refresh_from_db()

        self.assertEqual(
            period.field_20,
            Decimal('1660.00'),
        )

        self.assertEqual(
            period.field_17,
            Decimal('1660.00'),
        )

        self.assertEqual(
            period.field_15,
            Decimal('1660.00'),
        )

        self.assertEqual(
            period.field_26,
            Decimal('16.60'),
        )

        report = self.report_service.monthly(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            report['total_gel'],
            Decimal('1660.00'),
        )

        self.assertEqual(
            report['count'],
            2,
        )

        self.assertEqual(
            report['categories']['cashless_20']['total_gel'],
            Decimal('1660.00'),
        )

        self.assertTrue(report['matches_tax_period'])

        with self.assertRaises(ValidationError):
            (
                self.payment_service.create_income_from_invoice(
                    invoice=invoice,
                    received_at=(self._received_at(21)),
                    financial_account=(self.gel_account),
                    amount=Decimal('310.00'),
                    declaration_category=('cashless_20'),
                    tax_period_deadline=(self.tax_deadline),
                    payment_method=('bank_transfer'),
                )
            )

        self.assertEqual(
            IncomeEntry.objects.count(),
            2,
        )

        self.assertEqual(
            InvoicePayment.objects.count(),
            1,
        )

        invoice.refresh_from_db()

        self.assertEqual(
            invoice.status,
            'paid',
        )

        final_summary = self.payment_service.get_summary(invoice=invoice)

        self.assertEqual(
            final_summary['remaining_amount'],
            Decimal('0.00'),
        )

        self.assertTrue(final_summary['is_paid'])
