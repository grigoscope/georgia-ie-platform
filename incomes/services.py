from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from exchange_rates.services import GELConversionService
from incomes.models import IncomeEntry
from taxes.services import TaxPeriodCalculationService


class IncomeCategoryService:
    """Определение рекомендуемой графы декларации."""

    ACCOUNT_TYPE_MAPPING = {
        'cash_register': 'cash_register_18',
        'physical_pos': 'physical_pos_19',
        'bank_account': 'cashless_20',
        'bank_card': 'cashless_20',
        'payment_system': 'cashless_20',
        'crypto_wallet': 'other_21',
        'other': 'other_21',
    }

    @classmethod
    def suggest(cls, financial_account):
        if financial_account.default_declaration_category:
            return financial_account.default_declaration_category

        return cls.ACCOUNT_TYPE_MAPPING.get(
            financial_account.type,
            'other_21',
        )


class IncomeService:
    """Бизнес-логика журнала доходов."""

    def __init__(self):
        self.conversion_service = GELConversionService()
        self.tax_service = TaxPeriodCalculationService()

    @transaction.atomic
    def create_income(
        self,
        *,
        user,
        received_at,
        description,
        financial_account,
        original_amount,
        original_currency,
        declaration_category,
        counterparty=None,
        payment_method='',
        document_number='',
        document_date=None,
        invoice=None,
        additional_info='',
        vat_amount=Decimal('0.00'),
        comment='',
        attachment=None,
        manual_rate_value=None,
        manual_rate_unit=1,
        manual_source='manual',
        ready_amount_gel=None,
        tax_period_deadline=None,
    ):
        self._validate_owners(
            user=user,
            financial_account=financial_account,
            counterparty=counterparty,
            invoice=invoice,
        )

        self._validate_category(declaration_category)

        conversion = self.conversion_service.convert(
            amount=original_amount,
            currency_code=original_currency.code,
            user=user,
            manual_rate_value=manual_rate_value,
            manual_rate_unit=manual_rate_unit,
            manual_source=manual_source,
            ready_amount_gel=ready_amount_gel,
            rate_date=received_at.date(),
        )

        income = IncomeEntry(
            user=user,
            received_at=received_at,
            description=description,
            additional_info=additional_info,
            counterparty=counterparty,
            financial_account=financial_account,
            payment_method=payment_method,
            document_number=document_number,
            document_date=document_date,
            invoice=invoice,
            original_amount=conversion['original_amount'],
            original_currency=original_currency,
            exchange_rate_value=conversion['rate_value'],
            exchange_rate_unit=conversion['rate_unit'],
            exchange_rate_source=conversion['source'],
            exchange_rate_date=conversion['rate_date'],
            exchange_rate_time=conversion['rate_time'],
            amount_gel=conversion['amount_gel'],
            declaration_category=declaration_category,
            vat_amount=vat_amount,
            comment=comment,
            attachment=attachment,
        )

        income.full_clean()
        income.save()

        self.tax_service.recalculate_from_month(
            user=user,
            year=received_at.year,
            month=received_at.month,
            deadline=tax_period_deadline,
        )

        return income

    @staticmethod
    def _validate_owners(
        *,
        user,
        financial_account,
        counterparty,
        invoice,
    ):
        if financial_account.user_id != user.id:
            raise ValidationError('Финансовый счёт принадлежит другому пользователю.')

        if counterparty and counterparty.user_id != user.id:
            raise ValidationError('Контрагент принадлежит другому пользователю.')

        if invoice and invoice.user_id != user.id:
            raise ValidationError('Инвойс принадлежит другому пользователю.')

    @staticmethod
    def _validate_category(category):
        valid_categories = {value for value, _ in IncomeEntry.DECLARATION_CATEGORIES}

        if category not in valid_categories:
            raise ValidationError('Некорректная категория декларации.')
