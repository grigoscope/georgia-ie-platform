import hashlib
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
)
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class InvoicePDFService:
    """Генерация PDF-инвойсов."""

    FONT_NAME = 'InvoiceFont'
    FONT_BOLD_NAME = 'InvoiceFontBold'

    def __init__(self):
        self._register_fonts()

    def generate(self, *, invoice):
        """Сгенерировать PDF и сохранить его в Invoice."""

        pdf_bytes = self._build_pdf(
            invoice=invoice,
        )

        checksum = hashlib.sha256(pdf_bytes).hexdigest()

        filename = f'invoice-{invoice.number}.pdf'

        invoice.pdf_file.save(
            filename,
            ContentFile(pdf_bytes),
            save=False,
        )

        invoice.pdf_checksum = checksum
        invoice.generated_at = timezone.now()

        invoice.save(
            update_fields=[
                'pdf_file',
                'pdf_checksum',
                'generated_at',
                'updated_at',
            ]
        )

        return invoice

    def _build_pdf(self, *, invoice):
        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=f'Invoice {invoice.number}',
            author=(
                invoice.seller_snapshot.get(
                    'business_name',
                    '',
                )
            ),
        )

        styles = self._styles()

        story = []

        self._add_header(
            story=story,
            invoice=invoice,
            styles=styles,
        )

        self._add_parties(
            story=story,
            invoice=invoice,
            styles=styles,
        )

        self._add_items(
            story=story,
            invoice=invoice,
            styles=styles,
        )

        self._add_totals(
            story=story,
            invoice=invoice,
            styles=styles,
        )

        self._add_payment_details(
            story=story,
            invoice=invoice,
            styles=styles,
        )

        self._add_signature(
            story=story,
            invoice=invoice,
            styles=styles,
        )

        self._add_notes(
            story=story,
            invoice=invoice,
            styles=styles,
        )

        document.build(
            story,
            onFirstPage=self._draw_page_number,
            onLaterPages=self._draw_page_number,
        )

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _add_header(
        self,
        *,
        story,
        invoice,
        styles,
    ):
        story.append(
            Paragraph(
                f'INVOICE № {invoice.number}',
                styles['title'],
            )
        )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        header_data = [
            [
                Paragraph(
                    'Issue date',
                    styles['label'],
                ),
                Paragraph(
                    invoice.issue_date.isoformat(),
                    styles['normal'],
                ),
            ]
        ]

        if invoice.due_date:
            header_data.append(
                [
                    Paragraph(
                        'Due date',
                        styles['label'],
                    ),
                    Paragraph(
                        invoice.due_date.isoformat(),
                        styles['normal'],
                    ),
                ]
            )

        if invoice.service_period_start or invoice.service_period_end:
            start = (
                invoice.service_period_start.isoformat() if invoice.service_period_start else '-'
            )

            end = invoice.service_period_end.isoformat() if invoice.service_period_end else '-'

            header_data.append(
                [
                    Paragraph(
                        'Service period',
                        styles['label'],
                    ),
                    Paragraph(
                        f'{start} - {end}',
                        styles['normal'],
                    ),
                ]
            )

        header_data.append(
            [
                Paragraph(
                    'Currency',
                    styles['label'],
                ),
                Paragraph(
                    invoice.currency.code,
                    styles['normal'],
                ),
            ]
        )

        table = Table(
            header_data,
            colWidths=[
                42 * mm,
                115 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        'VALIGN',
                        (0, 0),
                        (-1, -1),
                        'TOP',
                    ),
                    (
                        'BOTTOMPADDING',
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(table)

        story.append(
            Spacer(
                1,
                8 * mm,
            )
        )

    def _add_parties(
        self,
        *,
        story,
        invoice,
        styles,
    ):
        seller = invoice.seller_snapshot
        buyer = invoice.buyer_snapshot

        seller_text = self._party_text(
            title='Seller',
            data=seller,
            styles=styles,
        )

        buyer_text = self._party_text(
            title='Buyer',
            data=buyer,
            styles=styles,
        )

        table = Table(
            [
                [
                    seller_text,
                    buyer_text,
                ]
            ],
            colWidths=[
                78 * mm,
                78 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        'VALIGN',
                        (0, 0),
                        (-1, -1),
                        'TOP',
                    ),
                    (
                        'BOX',
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        'INNERGRID',
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.lightgrey,
                    ),
                    (
                        'LEFTPADDING',
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        'RIGHTPADDING',
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        'TOPPADDING',
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        'BOTTOMPADDING',
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                ]
            )
        )

        story.append(table)

        story.append(
            Spacer(
                1,
                8 * mm,
            )
        )

    def _add_items(
        self,
        *,
        story,
        invoice,
        styles,
    ):
        data = [
            [
                Paragraph(
                    '#',
                    styles['table_header'],
                ),
                Paragraph(
                    'Description',
                    styles['table_header'],
                ),
                Paragraph(
                    'Qty',
                    styles['table_header'],
                ),
                Paragraph(
                    'Unit',
                    styles['table_header'],
                ),
                Paragraph(
                    'Price',
                    styles['table_header'],
                ),
                Paragraph(
                    'Total',
                    styles['table_header'],
                ),
            ]
        ]

        items = invoice.invoice_items.all().order_by('position')

        for item in items:
            data.append(
                [
                    Paragraph(
                        str(item.position),
                        styles['normal'],
                    ),
                    Paragraph(
                        item.description,
                        styles['normal'],
                    ),
                    Paragraph(
                        str(item.quantity),
                        styles['right'],
                    ),
                    Paragraph(
                        item.unit,
                        styles['normal'],
                    ),
                    Paragraph(
                        self._money_text(item.unit_price),
                        styles['right'],
                    ),
                    Paragraph(
                        self._money_text(item.line_total),
                        styles['right'],
                    ),
                ]
            )

        table = Table(
            data,
            repeatRows=1,
            colWidths=[
                9 * mm,
                69 * mm,
                18 * mm,
                20 * mm,
                22 * mm,
                25 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        'BACKGROUND',
                        (0, 0),
                        (-1, 0),
                        colors.HexColor('#eeeeee'),
                    ),
                    (
                        'BOX',
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        'INNERGRID',
                        (0, 0),
                        (-1, -1),
                        0.25,
                        colors.lightgrey,
                    ),
                    (
                        'VALIGN',
                        (0, 0),
                        (-1, -1),
                        'TOP',
                    ),
                    (
                        'LEFTPADDING',
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        'RIGHTPADDING',
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        'TOPPADDING',
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        'BOTTOMPADDING',
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(table)

        story.append(
            Spacer(
                1,
                7 * mm,
            )
        )

    def _add_totals(
        self,
        *,
        story,
        invoice,
        styles,
    ):
        data = [
            [
                Paragraph(
                    'Subtotal',
                    styles['label'],
                ),
                Paragraph(
                    self._money_text(invoice.subtotal),
                    styles['right'],
                ),
            ]
        ]

        if invoice.discount_amount:
            data.append(
                [
                    Paragraph(
                        'Discount',
                        styles['label'],
                    ),
                    Paragraph(
                        self._money_text(invoice.discount_amount),
                        styles['right'],
                    ),
                ]
            )

        if invoice.extra_charge_amount:
            data.append(
                [
                    Paragraph(
                        'Extra charge',
                        styles['label'],
                    ),
                    Paragraph(
                        self._money_text(invoice.extra_charge_amount),
                        styles['right'],
                    ),
                ]
            )

        data.append(
            [
                Paragraph(
                    'TOTAL',
                    styles['bold'],
                ),
                Paragraph(
                    (f'{self._money_text(invoice.total_amount)} {invoice.currency.code}'),
                    styles['bold_right'],
                ),
            ]
        )

        table = Table(
            data,
            colWidths=[
                45 * mm,
                35 * mm,
            ],
            hAlign='RIGHT',
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        'VALIGN',
                        (0, 0),
                        (-1, -1),
                        'TOP',
                    ),
                    (
                        'TOPPADDING',
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        'BOTTOMPADDING',
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        story.append(table)

        if invoice.tax_reference_amount is not None:
            story.append(
                Spacer(
                    1,
                    3 * mm,
                )
            )

            story.append(
                Paragraph(
                    (
                        'Tax reference: '
                        f'{self._money_text(invoice.tax_reference_amount)} '
                        f'{invoice.currency.code}'
                    ),
                    styles['normal'],
                )
            )

        if invoice.tax_note:
            story.append(
                Paragraph(
                    invoice.tax_note,
                    styles['normal'],
                )
            )

        story.append(
            Spacer(
                1,
                8 * mm,
            )
        )

    def _add_payment_details(
        self,
        *,
        story,
        invoice,
        styles,
    ):
        details = invoice.payment_details_snapshot or {}

        story.append(
            Paragraph(
                'Payment details',
                styles['section'],
            )
        )

        rows = []

        mapping = [
            ('Bank / provider', 'provider_name'),
            ('Account holder', 'account_holder'),
            ('IBAN', 'iban'),
            ('SWIFT / BIC', 'swift_bic'),
            (
                'Account identifier',
                'account_identifier',
            ),
            ('Crypto asset', 'crypto_asset'),
            ('Network', 'crypto_network'),
            ('Wallet', 'wallet_address'),
            ('Memo / Tag', 'memo_tag'),
        ]

        for label, key in mapping:
            value = details.get(key)

            if value:
                rows.append(
                    [
                        Paragraph(
                            label,
                            styles['label'],
                        ),
                        Paragraph(
                            str(value),
                            styles['normal'],
                        ),
                    ]
                )

        instructions = details.get('payment_instructions')

        if instructions:
            rows.append(
                [
                    Paragraph(
                        'Instructions',
                        styles['label'],
                    ),
                    Paragraph(
                        instructions,
                        styles['normal'],
                    ),
                ]
            )

        if invoice.payment_purpose:
            rows.append(
                [
                    Paragraph(
                        'Payment purpose',
                        styles['label'],
                    ),
                    Paragraph(
                        invoice.payment_purpose,
                        styles['normal'],
                    ),
                ]
            )

        if not rows:
            story.append(
                Paragraph(
                    'No payment details provided.',
                    styles['normal'],
                )
            )
            return

        table = Table(
            rows,
            colWidths=[
                42 * mm,
                115 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        'VALIGN',
                        (0, 0),
                        (-1, -1),
                        'TOP',
                    ),
                    (
                        'BOTTOMPADDING',
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(table)

    def _add_notes(
        self,
        *,
        story,
        invoice,
        styles,
    ):
        if not invoice.notes:
            return

        story.append(
            Spacer(
                1,
                7 * mm,
            )
        )

        story.append(
            KeepTogether(
                [
                    Paragraph(
                        'Notes',
                        styles['section'],
                    ),
                    Paragraph(
                        invoice.notes,
                        styles['normal'],
                    ),
                ]
            )
        )

    def _add_signature(
        self,
        *,
        story,
        invoice,
        styles,
    ):
        """Добавить подпись предпринимателя в PDF."""

        try:
            profile = invoice.user.entrepreneur_profile
        except AttributeError:
            return

        signature_file = profile.signature_file

        if not signature_file:
            return

        signature_file.open('rb')

        try:
            signature_bytes = BytesIO(signature_file.read())
        finally:
            signature_file.close()

        try:
            image = RLImage(signature_bytes)

            image._restrictSize(
                55 * mm,
                25 * mm,
            )

        except Exception:
            # Некорректная подпись не должна
            # ломать весь инвойс.
            return

        story.append(
            Spacer(
                1,
                6 * mm,
            )
        )

        story.append(
            Paragraph(
                'Signature',
                styles['section'],
            )
        )

        story.append(
            Spacer(
                1,
                2 * mm,
            )
        )

        story.append(image)

        seller_name = invoice.seller_snapshot.get(
            'business_name',
            '',
        )

        if seller_name:
            story.append(
                Spacer(
                    1,
                    2 * mm,
                )
            )

            story.append(
                Paragraph(
                    seller_name,
                    styles['normal'],
                )
            )

    def _party_text(
        self,
        *,
        title,
        data,
        styles,
    ):
        elements = [
            Paragraph(
                title,
                styles['section'],
            )
        ]

        preferred_keys = [
            ('business_name', 'Name'),
            ('name', 'Name'),
            (
                'entrepreneur_status',
                'Status',
            ),
            ('tin', 'TIN'),
            ('tax_id', 'Tax ID'),
            ('country', 'Country'),
            ('legal_address', 'Address'),
            ('address', 'Address'),
            ('email', 'Email'),
            ('phone', 'Phone'),
        ]

        for key, label in preferred_keys:
            value = data.get(key)

            if not value:
                continue

            elements.append(
                Paragraph(
                    f'<b>{label}:</b> {value}',
                    styles['normal'],
                )
            )

        return elements

    def _styles(self):
        base = getSampleStyleSheet()

        return {
            'title': ParagraphStyle(
                'InvoiceTitle',
                parent=base['Title'],
                fontName=self.FONT_BOLD_NAME,
                fontSize=18,
                leading=22,
                alignment=TA_LEFT,
                spaceAfter=4,
            ),
            'section': ParagraphStyle(
                'InvoiceSection',
                parent=base['Heading3'],
                fontName=self.FONT_BOLD_NAME,
                fontSize=11,
                leading=14,
                spaceAfter=5,
            ),
            'normal': ParagraphStyle(
                'InvoiceNormal',
                parent=base['Normal'],
                fontName=self.FONT_NAME,
                fontSize=9,
                leading=12,
            ),
            'label': ParagraphStyle(
                'InvoiceLabel',
                parent=base['Normal'],
                fontName=self.FONT_BOLD_NAME,
                fontSize=9,
                leading=12,
            ),
            'bold': ParagraphStyle(
                'InvoiceBold',
                parent=base['Normal'],
                fontName=self.FONT_BOLD_NAME,
                fontSize=10,
                leading=13,
            ),
            'right': ParagraphStyle(
                'InvoiceRight',
                parent=base['Normal'],
                fontName=self.FONT_NAME,
                fontSize=9,
                leading=12,
                alignment=TA_RIGHT,
            ),
            'bold_right': ParagraphStyle(
                'InvoiceBoldRight',
                parent=base['Normal'],
                fontName=self.FONT_BOLD_NAME,
                fontSize=10,
                leading=13,
                alignment=TA_RIGHT,
            ),
            'table_header': ParagraphStyle(
                'InvoiceTableHeader',
                parent=base['Normal'],
                fontName=self.FONT_BOLD_NAME,
                fontSize=8,
                leading=10,
            ),
        }

    @classmethod
    def _register_fonts(cls):
        if cls.FONT_NAME not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(
                TTFont(
                    cls.FONT_NAME,
                    settings.INVOICE_PDF_FONT_PATH,
                )
            )

        if cls.FONT_BOLD_NAME not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(
                TTFont(
                    cls.FONT_BOLD_NAME,
                    settings.INVOICE_PDF_FONT_BOLD_PATH,
                )
            )

    @staticmethod
    def _money_text(value):
        return f'{value:.2f}'

    @staticmethod
    def _draw_page_number(
        canvas,
        document,
    ):
        canvas.saveState()

        canvas.setFont(
            InvoicePDFService.FONT_NAME,
            8,
        )

        canvas.drawRightString(
            A4[0] - 18 * mm,
            10 * mm,
            f'Page {document.page}',
        )

        canvas.restoreState()
