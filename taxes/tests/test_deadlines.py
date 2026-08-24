from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import FinancialAccount
from incomes.models import IncomeEntry
from taxes.deadlines import TaxDeadlineService
from taxes.services import TaxPeriodCalculationService

User = get_user_model()


class TaxDeadlineServiceTests(TestCase):
    """Тесты расчёта налогового deadline."""

    def test_regular_month(self):
        deadline = TaxDeadlineService.calculate(
            year=2026,
            month=8,
        )

        self.assertEqual(
            deadline,
            date(2026, 9, 15),
        )

    def test_december_rolls_to_next_year(self):
        deadline = TaxDeadlineService.calculate(
            year=2026,
            month=12,
        )

        self.assertEqual(
            deadline,
            date(2027, 1, 15),
        )

    def test_january(self):
        deadline = TaxDeadlineService.calculate(
            year=2026,
            month=1,
        )

        self.assertEqual(
            deadline,
            date(2026, 2, 15),
        )

    def test_invalid_month(self):
        with self.assertRaises(ValidationError):
            TaxDeadlineService.calculate(
                year=2026,
                month=13,
            )


class AutomaticTaxPeriodDeadlineTests(TestCase):
    """Deadline автоматически попадает в TaxPeriod."""

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
        )

        self.service = TaxPeriodCalculationService()

    def _create_income(
        self,
        *,
        month,
        amount='100.00',
    ):
        received_at = timezone.make_aware(
            datetime(
                2026,
                month,
                10,
                12,
                0,
            )
        )

        return IncomeEntry.objects.create(
            user=self.user,
            received_at=received_at,
            description='Test income',
            financial_account=self.account,
            original_amount=Decimal(amount),
            original_currency=self.gel,
            exchange_rate_value=(Decimal('1')),
            exchange_rate_unit=1,
            exchange_rate_source='GEL',
            exchange_rate_date=(received_at.date()),
            amount_gel=Decimal(amount),
            declaration_category=('cashless_20'),
        )

    def test_period_gets_automatic_deadline(
        self,
    ):
        self._create_income(month=8)

        period = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            period.deadline,
            date(2026, 9, 15),
        )

    def test_december_period_deadline(
        self,
    ):
        self._create_income(month=12)

        period = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=12,
        )

        self.assertEqual(
            period.deadline,
            date(2027, 1, 15),
        )

    def test_explicit_deadline_can_override_default(
        self,
    ):
        self._create_income(month=8)

        custom_deadline = date(
            2026,
            9,
            20,
        )

        period = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
            deadline=custom_deadline,
        )

        self.assertEqual(
            period.deadline,
            custom_deadline,
        )
