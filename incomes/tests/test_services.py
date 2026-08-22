from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import EntrepreneurProfile
from audit.models import AuditLog
from exchange_rates.models import Currency, ExchangeRate
from finances.models import FinancialAccount
from incomes.models import IncomeEntry
from incomes.services import (
    IncomeCategoryService,
    IncomeService,
)
from taxes.models import TaxPeriod

User = get_user_model()


class IncomeServiceTests(TestCase):
    """Тесты сервиса создания доходов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            tin='123456789',
            tax_rate=Decimal('1.00'),
        )

        self.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            kind='fiat',
            decimal_places=2,
        )

        self.account = FinancialAccount.objects.create(
            user=self.user,
            name='TBC USD',
            type='bank_account',
            default_currency=self.usd,
        )

        self.received_at = timezone.make_aware(
            datetime(
                2026,
                8,
                21,
                12,
                0,
            )
        )

        self.deadline = date(
            2026,
            9,
            15,
        )

        self.service = IncomeService()

    def test_category_suggestion_for_bank_account(self):
        category = IncomeCategoryService.suggest(self.account)

        self.assertEqual(
            category,
            'cashless_20',
        )

    def test_create_income_with_manual_usd_rate(self):
        income = self.service.create_income(
            user=self.user,
            received_at=self.received_at,
            description='Разработка сайта',
            financial_account=self.account,
            original_amount=Decimal('500.00'),
            original_currency=self.usd,
            declaration_category='cashless_20',
            manual_rate_value=Decimal('2.70'),
            manual_source='test_manual',
            tax_period_deadline=self.deadline,
        )

        self.assertEqual(
            income.original_amount,
            Decimal('500.00'),
        )

        self.assertEqual(
            income.exchange_rate_value,
            Decimal('2.70'),
        )

        self.assertEqual(
            income.amount_gel,
            Decimal('1350.00'),
        )

        self.assertEqual(
            income.declaration_category,
            'cashless_20',
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

    def test_tax_period_created_after_income(self):
        self.service.create_income(
            user=self.user,
            received_at=self.received_at,
            description='Разработка сайта',
            financial_account=self.account,
            original_amount=Decimal('500'),
            original_currency=self.usd,
            declaration_category='cashless_20',
            manual_rate_value=Decimal('2.70'),
            tax_period_deadline=self.deadline,
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

    def test_audit_log_created(self):
        income = self.service.create_income(
            user=self.user,
            received_at=self.received_at,
            description='Консультация',
            financial_account=self.account,
            original_amount=Decimal('100'),
            original_currency=self.usd,
            declaration_category='cashless_20',
            manual_rate_value=Decimal('2.70'),
            tax_period_deadline=self.deadline,
        )

        audit = AuditLog.objects.get(
            object_type='IncomeEntry',
            object_id=income.pk,
            action='create',
        )

        self.assertEqual(
            audit.user,
            self.user,
        )

        self.assertEqual(
            audit.actor,
            self.user,
        )

        self.assertEqual(
            audit.new_values['amount_gel'],
            '270.00',
        )

        self.assertEqual(
            audit.new_values['declaration_category'],
            'cashless_20',
        )

    def test_user_can_choose_different_category(self):
        income = self.service.create_income(
            user=self.user,
            received_at=self.received_at,
            description='Прочий доход',
            financial_account=self.account,
            original_amount=Decimal('100'),
            original_currency=self.usd,
            declaration_category='other_21',
            manual_rate_value=Decimal('2.70'),
            tax_period_deadline=self.deadline,
        )

        self.assertEqual(
            income.declaration_category,
            'other_21',
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            period.field_20,
            Decimal('0.00'),
        )

        self.assertEqual(
            period.field_21,
            Decimal('270.00'),
        )

    def test_foreign_financial_account_is_rejected(self):
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpassword123',
        )

        other_account = FinancialAccount.objects.create(
            user=other_user,
            name='Foreign Account',
            type='bank_account',
            default_currency=self.usd,
        )

        with self.assertRaises(ValidationError):
            self.service.create_income(
                user=self.user,
                received_at=self.received_at,
                description='Чужой счёт',
                financial_account=other_account,
                original_amount=Decimal('500'),
                original_currency=self.usd,
                declaration_category='cashless_20',
                manual_rate_value=Decimal('2.70'),
                tax_period_deadline=self.deadline,
            )

        self.assertEqual(
            IncomeEntry.objects.count(),
            0,
        )

        self.assertEqual(
            TaxPeriod.objects.count(),
            0,
        )

        self.assertEqual(
            AuditLog.objects.count(),
            0,
        )

    def test_transaction_rolls_back_if_tax_period_fails(self):
        with self.assertRaises(ValidationError):
            self.service.create_income(
                user=self.user,
                received_at=self.received_at,
                description='Без deadline',
                financial_account=self.account,
                original_amount=Decimal('500'),
                original_currency=self.usd,
                declaration_category='cashless_20',
                manual_rate_value=Decimal('2.70'),
            )

        self.assertEqual(
            IncomeEntry.objects.count(),
            0,
        )

        self.assertEqual(
            TaxPeriod.objects.count(),
            0,
        )

        self.assertEqual(
            AuditLog.objects.count(),
            0,
        )

        self.assertEqual(
            ExchangeRate.objects.count(),
            0,
        )