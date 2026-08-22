from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from audit.services import AuditService
from exchange_rates.services import GELConversionService
from incomes.models import IncomeEntry
from taxes.models import TaxPeriod
from taxes.services import TaxPeriodCalculationService

UNSET = object()


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
        self.audit_service = AuditService()

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
        actor=None,
        request_id='',
        ip_address=None,
        user_agent='',
    ):
        """Создать доход."""

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

        self.audit_service.log(
            user=user,
            actor=actor or user,
            action='create',
            obj=income,
            new_values=self._audit_values(income),
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return income

    @transaction.atomic
    def update_income(
        self,
        *,
        income,
        description=None,
        received_at=None,
        financial_account=None,
        counterparty=UNSET,
        invoice=UNSET,
        declaration_category=None,
        comment=None,
        additional_info=None,
        payment_method=None,
        document_number=None,
        document_date=UNSET,
        tax_period_deadline=None,
        actor=None,
        request_id='',
        ip_address=None,
        user_agent='',
    ):
        """Изменить доход."""

        if income.is_deleted:
            raise ValidationError('Нельзя изменить удалённый доход.')

        user = income.user

        old_year = income.received_at.year
        old_month = income.received_at.month

        old_values = self._audit_values(income)

        new_received_at = received_at if received_at is not None else income.received_at

        new_financial_account = (
            financial_account if financial_account is not None else income.financial_account
        )

        new_counterparty = income.counterparty if counterparty is UNSET else counterparty

        new_invoice = income.invoice if invoice is UNSET else invoice

        new_category = (
            declaration_category
            if declaration_category is not None
            else income.declaration_category
        )

        self._validate_owners(
            user=user,
            financial_account=new_financial_account,
            counterparty=new_counterparty,
            invoice=new_invoice,
        )

        self._validate_category(new_category)

        if description is not None:
            income.description = description

        income.received_at = new_received_at
        income.financial_account = new_financial_account
        income.counterparty = new_counterparty
        income.invoice = new_invoice
        income.declaration_category = new_category

        if comment is not None:
            income.comment = comment

        if additional_info is not None:
            income.additional_info = additional_info

        if payment_method is not None:
            income.payment_method = payment_method

        if document_number is not None:
            income.document_number = document_number

        if document_date is not UNSET:
            income.document_date = document_date

        income.full_clean()
        income.save()

        new_year = income.received_at.year
        new_month = income.received_at.month

        self._recalculate_after_change(
            user=user,
            old_year=old_year,
            old_month=old_month,
            new_year=new_year,
            new_month=new_month,
            tax_period_deadline=tax_period_deadline,
        )

        self.audit_service.log(
            user=user,
            actor=actor or user,
            action='update',
            obj=income,
            old_values=old_values,
            new_values=self._audit_values(income),
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return income

    @transaction.atomic
    def delete_income(
        self,
        *,
        income,
        actor=None,
        request_id='',
        ip_address=None,
        user_agent='',
    ):
        """Мягко удалить доход."""

        if income.is_deleted:
            raise ValidationError('Доход уже удалён.')

        user = income.user

        old_values = self._audit_values(income)

        income.is_deleted = True
        income.deleted_at = timezone.now()

        income.save(
            update_fields=[
                'is_deleted',
                'deleted_at',
                'updated_at',
            ]
        )

        self.tax_service.recalculate_from_month(
            user=user,
            year=income.received_at.year,
            month=income.received_at.month,
        )

        self.audit_service.log(
            user=user,
            actor=actor or user,
            action='delete',
            obj=income,
            old_values=old_values,
            new_values=self._audit_values(income),
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return income

    def _recalculate_after_change(
        self,
        *,
        user,
        old_year,
        old_month,
        new_year,
        new_month,
        tax_period_deadline=None,
    ):
        """Пересчитать налоговые периоды после изменения дохода."""

        if old_year == new_year and old_month == new_month:
            self.tax_service.recalculate_from_month(
                user=user,
                year=old_year,
                month=old_month,
            )

            return

        self.tax_service.recalculate_from_month(
            user=user,
            year=old_year,
            month=old_month,
        )

        new_period_exists = TaxPeriod.objects.filter(
            user=user,
            year=new_year,
            month=new_month,
        ).exists()

        if not new_period_exists and tax_period_deadline is None:
            raise ValidationError('Для нового налогового периода необходимо указать deadline.')

        self.tax_service.recalculate_from_month(
            user=user,
            year=new_year,
            month=new_month,
            deadline=(tax_period_deadline if not new_period_exists else None),
        )

    @staticmethod
    def _audit_values(income):
        """Данные IncomeEntry для журнала аудита."""

        return {
            'received_at': income.received_at,
            'description': income.description,
            'counterparty': income.counterparty,
            'financial_account': income.financial_account,
            'original_amount': income.original_amount,
            'original_currency': income.original_currency,
            'exchange_rate_value': income.exchange_rate_value,
            'exchange_rate_unit': income.exchange_rate_unit,
            'exchange_rate_source': income.exchange_rate_source,
            'exchange_rate_date': income.exchange_rate_date,
            'amount_gel': income.amount_gel,
            'declaration_category': income.declaration_category,
            'vat_amount': income.vat_amount,
            'invoice': income.invoice,
            'comment': income.comment,
            'is_deleted': income.is_deleted,
            'deleted_at': income.deleted_at,
        }

    @staticmethod
    def _validate_owners(
        *,
        user,
        financial_account,
        counterparty,
        invoice,
    ):
        """Проверить принадлежность связанных объектов."""

        if financial_account.user_id != user.id:
            raise ValidationError('Финансовый счёт принадлежит другому пользователю.')

        if counterparty and counterparty.user_id != user.id:
            raise ValidationError('Контрагент принадлежит другому пользователю.')

        if invoice and invoice.user_id != user.id:
            raise ValidationError('Инвойс принадлежит другому пользователю.')

    @staticmethod
    def _validate_category(category):
        """Проверить графу декларации."""

        valid_categories = {value for value, _ in IncomeEntry.DECLARATION_CATEGORIES}

        if category not in valid_categories:
            raise ValidationError('Некорректная категория декларации.')
