from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from incomes.services import (
    IncomeCategoryService,
    IncomeService,
)
from invoices.models import Invoice, InvoicePayment


class InvoicePaymentService:
    """Бизнес-логика оплат инвойсов."""

    MONEY_QUANT = Decimal('0.01')

    def __init__(self):
        self.income_service = IncomeService()

    def get_summary(self, *, invoice):
        """Получить информацию об оплате инвойса."""

        result = invoice.payments.aggregate(
            total=Sum(
                'amount',
                default=Decimal('0.00'),
            )
        )

        paid_amount = self._money(result['total'])

        total_amount = self._money(invoice.total_amount)

        remaining_amount = self._money(total_amount - paid_amount)

        if remaining_amount < 0:
            remaining_amount = Decimal('0.00')

        return {
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'remaining_amount': remaining_amount,
            'is_paid': remaining_amount == 0,
        }

    @transaction.atomic
    def register_income_payment(
        self,
        *,
        invoice,
        income_entry,
    ):
        """
        Связать уже существующий доход
        с оплатой инвойса.
        """

        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)

        self._validate_invoice(invoice=invoice)

        self._validate_income(
            invoice=invoice,
            income_entry=income_entry,
        )

        if InvoicePayment.objects.filter(
            invoice=invoice,
            income_entry=income_entry,
        ).exists():
            raise ValidationError('Этот доход уже зарегистрирован как оплата данного инвойса.')

        summary = self.get_summary(invoice=invoice)

        if summary['remaining_amount'] <= 0:
            raise ValidationError('Инвойс уже полностью оплачен.')

        payment_amount = self._money(income_entry.original_amount)

        if payment_amount > summary['remaining_amount']:
            raise ValidationError('Сумма оплаты превышает остаток по инвойсу.')

        payment = InvoicePayment(
            invoice=invoice,
            income_entry=income_entry,
            amount=payment_amount,
            currency=income_entry.original_currency,
            paid_at=income_entry.received_at,
        )

        payment.full_clean()
        payment.save()

        if income_entry.invoice_id is None:
            income_entry.invoice = invoice

            income_entry.save(
                update_fields=[
                    'invoice',
                    'updated_at',
                ]
            )

        self._update_invoice_status(
            invoice=invoice,
        )

        return payment

    @transaction.atomic
    def create_income_from_invoice(
        self,
        *,
        invoice,
        received_at,
        financial_account,
        amount,
        declaration_category,
        tax_period_deadline=None,
        payment_method='',
        manual_rate_value=None,
        manual_rate_unit=1,
        manual_source='manual',
        ready_amount_gel=None,
        comment='',
        actor=None,
        request_id='',
        ip_address=None,
        user_agent='',
    ):
        """
        Создать IncomeEntry из фактической
        оплаты инвойса и связать его с InvoicePayment.
        """

        invoice = (
            Invoice.objects.select_for_update()
            .select_related(
                'currency',
                'counterparty',
            )
            .get(pk=invoice.pk)
        )

        self._validate_invoice(invoice=invoice)

        summary = self.get_summary(invoice=invoice)

        if summary['remaining_amount'] <= 0:
            raise ValidationError('Инвойс уже полностью оплачен.')

        amount = self._money(amount)

        if amount <= 0:
            raise ValidationError('Сумма оплаты должна быть больше нуля.')

        if amount > summary['remaining_amount']:
            raise ValidationError('Сумма оплаты превышает остаток по инвойсу.')

        if declaration_category is None:
            declaration_category = IncomeCategoryService.suggest(financial_account)

        income = self.income_service.create_income(
            user=invoice.user,
            received_at=received_at,
            description=(f'Оплата по инвойсу {invoice.number}'),
            additional_info='',
            counterparty=invoice.counterparty,
            financial_account=financial_account,
            payment_method=payment_method,
            document_number=invoice.number,
            document_date=invoice.issue_date,
            invoice=invoice,
            original_amount=amount,
            original_currency=invoice.currency,
            declaration_category=declaration_category,
            comment=comment,
            manual_rate_value=manual_rate_value,
            manual_rate_unit=manual_rate_unit,
            manual_source=manual_source,
            ready_amount_gel=ready_amount_gel,
            tax_period_deadline=tax_period_deadline,
            actor=actor or invoice.user,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        payment = self.register_income_payment(
            invoice=invoice,
            income_entry=income,
        )

        invoice.refresh_from_db()

        return {
            'invoice': invoice,
            'income': income,
            'payment': payment,
            'summary': self.get_summary(invoice=invoice),
        }

    @transaction.atomic
    def _update_invoice_status(
        self,
        *,
        invoice,
    ):
        """Обновить статус после оплаты."""

        summary = self.get_summary(invoice=invoice)

        if summary['paid_amount'] <= 0:
            return invoice

        if summary['remaining_amount'] == 0:
            last_payment = invoice.payments.order_by('-paid_at').first()

            invoice.status = 'paid'

            invoice.paid_at = last_payment.paid_at if last_payment else timezone.now()

        else:
            invoice.status = 'partially_paid'
            invoice.paid_at = None

        invoice.save(
            update_fields=[
                'status',
                'paid_at',
                'updated_at',
            ]
        )

        return invoice

    @staticmethod
    def _validate_invoice(*, invoice):
        if invoice.status == 'cancelled':
            raise ValidationError('Нельзя зарегистрировать оплату отменённого инвойса.')

        if invoice.status == 'paid':
            raise ValidationError('Инвойс уже полностью оплачен.')

    @staticmethod
    def _validate_income(
        *,
        invoice,
        income_entry,
    ):
        if income_entry.user_id != invoice.user_id:
            raise ValidationError('Доход принадлежит другому пользователю.')

        if income_entry.is_deleted:
            raise ValidationError('Удалённый доход нельзя использовать как оплату инвойса.')

        if income_entry.invoice_id is not None and income_entry.invoice_id != invoice.id:
            raise ValidationError('Доход уже связан с другим инвойсом.')

        if income_entry.original_currency_id != invoice.currency_id:
            raise ValidationError('Валюта дохода должна совпадать с валютой инвойса.')

    @classmethod
    def _money(cls, value):
        return Decimal(str(value)).quantize(
            cls.MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )
