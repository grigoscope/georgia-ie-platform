from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import Counterparty, FinancialAccount
from invoices.models import Invoice, InvoiceItem
from invoices.services import InvoiceService

User = get_user_model()


class InvoiceServiceTests(TestCase):
    """Тесты сервиса инвойсов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )

        self.profile = EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Entrepreneur',
            tin='123456789',
            tax_rate=Decimal('1.00'),
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
            name='Other account',
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
            phone='+995555000000',
        )

        self.other_counterparty = Counterparty.objects.create(
            user=self.other_user,
            name='Foreign Client',
            type='company',
        )

        self.service = InvoiceService()

        self.items = [
            {
                'description': 'Backend development',
                'quantity': '2',
                'unit': 'hour',
                'unit_price': '100.00',
            },
            {
                'description': 'Consulting',
                'quantity': '1',
                'unit': 'service',
                'unit_price': '110.00',
            },
        ]

    def _create_invoice(self, **kwargs):
        data = {
            'user': self.user,
            'issue_date': date(2026, 8, 22),
            'currency': self.gel,
            'counterparty': self.counterparty,
            'financial_account': self.account,
            'items': self.items,
        }

        data.update(kwargs)

        return self.service.create_invoice(**data)

    def test_create_invoice_calculates_totals(self):
        invoice = self._create_invoice()

        self.assertEqual(
            invoice.subtotal,
            Decimal('310.00'),
        )

        self.assertEqual(
            invoice.discount_amount,
            Decimal('0.00'),
        )

        self.assertEqual(
            invoice.extra_charge_amount,
            Decimal('0.00'),
        )

        self.assertEqual(
            invoice.total_amount,
            Decimal('310.00'),
        )

        self.assertEqual(
            invoice.status,
            'draft',
        )

        self.assertEqual(
            Invoice.objects.count(),
            1,
        )

        self.assertEqual(
            InvoiceItem.objects.count(),
            2,
        )

    def test_invoice_items_are_calculated(self):
        invoice = self._create_invoice()

        items = list(invoice.invoice_items.order_by('position'))

        self.assertEqual(
            len(items),
            2,
        )

        first = items[0]

        self.assertEqual(
            first.position,
            1,
        )

        self.assertEqual(
            first.description,
            'Backend development',
        )

        self.assertEqual(
            first.quantity,
            Decimal('2.000'),
        )

        self.assertEqual(
            first.unit_price,
            Decimal('100.00'),
        )

        self.assertEqual(
            first.line_total,
            Decimal('200.00'),
        )

        second = items[1]

        self.assertEqual(
            second.position,
            2,
        )

        self.assertEqual(
            second.line_total,
            Decimal('110.00'),
        )

    def test_discount_and_extra_charge(self):
        invoice = self._create_invoice(
            discount=Decimal('20.00'),
            extra_charge=Decimal('10.00'),
        )

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

    def test_tax_reference_does_not_change_total(self):
        invoice = self._create_invoice(
            tax_reference_amount=Decimal('3.10'),
            tax_note='Reference tax only',
        )

        self.assertEqual(
            invoice.tax_reference_amount,
            Decimal('3.10'),
        )

        self.assertEqual(
            invoice.total_amount,
            Decimal('310.00'),
        )

    def test_seller_snapshot_is_saved(self):
        invoice = self._create_invoice()

        self.assertEqual(
            invoice.seller_snapshot['business_name'],
            'Test Entrepreneur',
        )

        self.assertEqual(
            invoice.seller_snapshot['tin'],
            '123456789',
        )

        self.assertEqual(
            invoice.seller_snapshot['email'],
            'user@example.com',
        )

    def test_buyer_snapshot_is_saved(self):
        invoice = self._create_invoice()

        self.assertEqual(
            invoice.buyer_snapshot['name'],
            'Client LLC',
        )

        self.assertEqual(
            invoice.buyer_snapshot['tax_id'],
            '111222333',
        )

        self.assertEqual(
            invoice.buyer_snapshot['country'],
            'Georgia',
        )

        self.assertEqual(
            invoice.buyer_snapshot['address'],
            'Tbilisi',
        )

    def test_payment_details_snapshot_is_saved(self):
        invoice = self._create_invoice()

        details = invoice.payment_details_snapshot

        self.assertEqual(
            details['name'],
            'TBC GEL',
        )

        self.assertEqual(
            details['type'],
            'bank_account',
        )

        self.assertEqual(
            details['provider_name'],
            'TBC Bank',
        )

        self.assertEqual(
            details['iban'],
            'GE00TB0000000000000000',
        )

        self.assertEqual(
            details['currency'],
            'GEL',
        )

    def test_snapshot_does_not_change_after_counterparty_update(self):
        invoice = self._create_invoice()

        self.counterparty.name = 'New Client Name'
        self.counterparty.address = 'Batumi'
        self.counterparty.save()

        invoice.refresh_from_db()

        self.assertEqual(
            invoice.buyer_snapshot['name'],
            'Client LLC',
        )

        self.assertEqual(
            invoice.buyer_snapshot['address'],
            'Tbilisi',
        )

    def test_invoice_numbers_increment(self):
        first = self._create_invoice()
        second = self._create_invoice()

        self.assertEqual(
            first.number,
            'INV-1',
        )

        self.assertEqual(
            second.number,
            'INV-2',
        )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.next_invoice_number,
            3,
        )

    def test_invoice_requires_items(self):
        with self.assertRaises(ValidationError):
            self._create_invoice(
                items=[],
            )

        self.assertEqual(
            Invoice.objects.count(),
            0,
        )

    def test_item_requires_description(self):
        with self.assertRaises(ValidationError):
            self._create_invoice(
                items=[
                    {
                        'description': '',
                        'quantity': '1',
                        'unit_price': '100',
                    }
                ],
            )

        self.assertEqual(
            Invoice.objects.count(),
            0,
        )

    def test_quantity_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self._create_invoice(
                items=[
                    {
                        'description': 'Service',
                        'quantity': '0',
                        'unit_price': '100',
                    }
                ],
            )

        self.assertEqual(
            Invoice.objects.count(),
            0,
        )

    def test_unit_price_cannot_be_negative(self):
        with self.assertRaises(ValidationError):
            self._create_invoice(
                items=[
                    {
                        'description': 'Service',
                        'quantity': '1',
                        'unit_price': '-100',
                    }
                ],
            )

        self.assertEqual(
            Invoice.objects.count(),
            0,
        )

    def test_total_cannot_be_negative(self):
        with self.assertRaises(ValidationError):
            self._create_invoice(
                discount=Decimal('500.00'),
            )

        self.assertEqual(
            Invoice.objects.count(),
            0,
        )

    def test_foreign_counterparty_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._create_invoice(
                counterparty=(self.other_counterparty),
            )

        self.assertEqual(
            Invoice.objects.count(),
            0,
        )

    def test_foreign_financial_account_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._create_invoice(
                financial_account=(self.other_account),
            )

        self.assertEqual(
            Invoice.objects.count(),
            0,
        )

    def test_failed_invoice_does_not_consume_number(self):
        with self.assertRaises(ValidationError):
            self._create_invoice(
                discount=Decimal('9999'),
            )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.next_invoice_number,
            1,
        )

        invoice = self._create_invoice()

        self.assertEqual(
            invoice.number,
            'INV-1',
        )
