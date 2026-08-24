import base64
import hashlib
import re
import tempfile
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import Counterparty, FinancialAccount
from invoices.pdf import InvoicePDFService
from invoices.services import InvoiceService

User = get_user_model()


class InvoicePDFServiceTests(TestCase):
    """Тесты генерации PDF-инвойса."""

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

        self.profile = EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='ООО Тестовый бизнес',
            entrepreneur_status='Individual Entrepreneur',
            tin='123456789',
            legal_address=(
                'Тбилиси, очень длинный юридический адрес для проверки переноса строк в PDF'
            ),
            phone='+995555123456',
            public_email='business@example.com',
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
            account_holder='ООО Тестовый бизнес',
            iban='GE00TB0000000000000000',
            swift_bic='TBCBGE22',
            payment_instructions=('Укажите номер инвойса в назначении платежа.'),
        )

        self.counterparty = Counterparty.objects.create(
            user=self.user,
            name='Клиент Тест',
            type='company',
            country='Georgia',
            tax_id='987654321',
            address=(
                'Тбилиси, проспект Руставели, '
                'очень длинный адрес клиента '
                'для проверки автоматического переноса'
            ),
            email='client@example.com',
            phone='+995555999999',
        )

        self.invoice_service = InvoiceService()
        self.pdf_service = InvoicePDFService()

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

    def _create_invoice(
        self,
        *,
        items=None,
        notes='',
    ):
        if items is None:
            items = [
                {
                    'description': ('Разработка backend-части платформы'),
                    'quantity': '2',
                    'unit': 'hour',
                    'unit_price': '100.00',
                },
                {
                    'description': 'Консультация',
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': '110.00',
                },
            ]

        return self.invoice_service.create_invoice(
            user=self.user,
            issue_date=date(2026, 8, 22),
            due_date=date(2026, 9, 5),
            currency=self.gel,
            counterparty=self.counterparty,
            financial_account=self.account,
            items=items,
            language='ru',
            tax_note=('Налог указан исключительно в справочных целях.'),
            tax_reference_amount=Decimal('3.10'),
            payment_purpose='Оплата по инвойсу',
            notes=notes,
        )

    def test_generate_pdf(self):
        invoice = self._create_invoice()

        self.pdf_service.generate(invoice=invoice)

        invoice.refresh_from_db()

        self.assertTrue(invoice.pdf_file)

        self.assertTrue(invoice.pdf_file.name.endswith('.pdf'))

        self.assertIsNotNone(invoice.generated_at)

        self.assertEqual(
            len(invoice.pdf_checksum),
            64,
        )

        with invoice.pdf_file.open('rb') as file:
            pdf_bytes = file.read()

        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

        self.assertGreater(
            len(pdf_bytes),
            1000,
        )

    def test_pdf_checksum_is_correct(self):
        invoice = self._create_invoice()

        self.pdf_service.generate(invoice=invoice)

        invoice.refresh_from_db()

        with invoice.pdf_file.open('rb') as file:
            pdf_bytes = file.read()

        expected_checksum = hashlib.sha256(pdf_bytes).hexdigest()

        self.assertEqual(
            invoice.pdf_checksum,
            expected_checksum,
        )

    def test_pdf_supports_cyrillic_and_georgian(self):
        """
        Проверяем, что Unicode-данные
        не ломают генерацию PDF.
        """

        self.profile.business_name = 'ИП Тест საქართველო'
        self.profile.legal_address = 'თბილისი, საქართველო'
        self.profile.save()

        self.counterparty.name = 'Клиент Тест ქართული'
        self.counterparty.address = 'Тбилиси, улица Руставели'
        self.counterparty.save()

        invoice = self._create_invoice(
            items=[
                {
                    'description': ('Разработка программного обеспечения — პროგრამული მომსახურება'),
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': '310.00',
                },
            ],
            notes=('Спасибо за сотрудничество. მადლობა თანამშრომლობისთვის.'),
        )

        self.assertIn(
            'საქართველო',
            invoice.seller_snapshot['business_name'],
        )

        self.pdf_service.generate(invoice=invoice)

        invoice.refresh_from_db()

        with invoice.pdf_file.open('rb') as file:
            pdf_bytes = file.read()

        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

        self.assertGreater(
            len(pdf_bytes),
            1000,
        )

    def test_pdf_handles_long_text(self):
        long_description = (
            'Очень длинное описание услуги, которое должно '
            'автоматически переноситься внутри таблицы PDF. '
            'Разработка backend-части платформы, интеграция '
            'внешних сервисов, тестирование и настройка системы.'
        )

        self.assertLessEqual(
            len(long_description),
            255,
        )

        invoice = self._create_invoice(
            items=[
                {
                    'description': long_description,
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': '310.00',
                },
            ],
            notes=(
                'Очень длинное примечание к инвойсу, '
                'которое должно автоматически переноситься '
                'на несколько строк при создании PDF. '
            )
            * 30,
        )

        self.pdf_service.generate(invoice=invoice)

        invoice.refresh_from_db()

        with invoice.pdf_file.open('rb') as file:
            pdf_bytes = file.read()

        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

        self.assertGreater(
            len(pdf_bytes),
            1000,
        )

    def test_pdf_with_many_items_has_multiple_pages(self):
        items = []

        for number in range(1, 81):
            items.append(
                {
                    'description': (f'Услуга №{number}: разработка программного обеспечения'),
                    'quantity': '1',
                    'unit': 'service',
                    'unit_price': '10.00',
                }
            )

        invoice = self._create_invoice(
            items=items,
        )

        self.assertEqual(
            invoice.invoice_items.count(),
            80,
        )

        self.assertEqual(
            invoice.total_amount,
            Decimal('800.00'),
        )

        self.pdf_service.generate(invoice=invoice)

        invoice.refresh_from_db()

        with invoice.pdf_file.open('rb') as file:
            pdf_bytes = file.read()

        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

        page_count = len(
            re.findall(
                rb'/Type\s*/Page\b',
                pdf_bytes,
            )
        )

        self.assertGreater(
            page_count,
            1,
        )

    def test_regeneration_updates_pdf(self):
        invoice = self._create_invoice()

        self.pdf_service.generate(invoice=invoice)

        invoice.refresh_from_db()

        first_checksum = invoice.pdf_checksum

        invoice.notes = 'Новое примечание перед повторной генерацией.'
        invoice.save(
            update_fields=[
                'notes',
                'updated_at',
            ]
        )

        self.pdf_service.generate(invoice=invoice)

        invoice.refresh_from_db()

        second_checksum = invoice.pdf_checksum

        self.assertNotEqual(
            first_checksum,
            second_checksum,
        )

    def test_pdf_contains_signature(self):
        signature_png = base64.b64decode(
            (
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB'
                'CAQAAAC1HAwCAAAAC0lEQVR42mNk'
                'YAAAAAYAAjCB0C8AAAAASUVORK5CYII='
            )
        )

        self.profile.signature_file.save(
            'signature.png',
            ContentFile(signature_png),
            save=True,
        )

        invoice = self._create_invoice()

        self.pdf_service.generate(invoice=invoice)

        invoice.refresh_from_db()

        with invoice.pdf_file.open('rb') as file:
            pdf_bytes = file.read()

        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

        self.assertIn(
            b'/Subtype /Image',
            pdf_bytes,
        )
