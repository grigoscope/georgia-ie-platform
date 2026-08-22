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
from taxes.models import TaxPeriod
from taxes.services import TaxPeriodCalculationService

User = get_user_model()


class TaxPeriodCalculationServiceTests(TestCase):
    """Тесты расчёта налоговых периодов."""

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
        amount,
        month,
        category,
        day=10,
        is_deleted=False,
    ):
        received_at = timezone.make_aware(
            datetime(
                2026,
                month,
                day,
                12,
                0,
            )
        )

        return IncomeEntry.objects.create(
            user=self.user,
            received_at=received_at,
            description='Test income',
            financial_account=self.account,
            original_amount=Decimal(str(amount)),
            original_currency=self.gel,
            exchange_rate_value=Decimal('1'),
            exchange_rate_unit=1,
            exchange_rate_source='GEL',
            exchange_rate_date=received_at.date(),
            amount_gel=Decimal(str(amount)),
            declaration_category=category,
            is_deleted=is_deleted,
        )

    def test_calculates_fields_18_to_21(self):
        self._create_income(
            amount='100',
            month=8,
            category='cash_register_18',
        )

        self._create_income(
            amount='200',
            month=8,
            category='physical_pos_19',
        )

        self._create_income(
            amount='300',
            month=8,
            category='cashless_20',
        )

        self._create_income(
            amount='400',
            month=8,
            category='other_21',
        )

        period = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
            deadline=date(2026, 9, 15),
        )

        self.assertEqual(
            period.field_18,
            Decimal('100.00'),
        )
        self.assertEqual(
            period.field_19,
            Decimal('200.00'),
        )
        self.assertEqual(
            period.field_20,
            Decimal('300.00'),
        )
        self.assertEqual(
            period.field_21,
            Decimal('400.00'),
        )

        self.assertEqual(
            period.field_17,
            Decimal('1000.00'),
        )

        self.assertEqual(
            period.field_26,
            Decimal('10.00'),
        )

    def test_cumulative_field_15(self):
        self._create_income(
            amount='1000',
            month=1,
            category='cashless_20',
        )

        self._create_income(
            amount='500',
            month=2,
            category='cashless_20',
        )

        january = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=1,
            deadline=date(2026, 2, 15),
        )

        february = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=2,
            deadline=date(2026, 3, 15),
        )

        self.assertEqual(
            january.field_17,
            Decimal('1000.00'),
        )

        self.assertEqual(
            january.field_15,
            Decimal('1000.00'),
        )

        self.assertEqual(
            february.field_17,
            Decimal('500.00'),
        )

        self.assertEqual(
            february.field_15,
            Decimal('1500.00'),
        )

    def test_zero_month_keeps_cumulative_total(self):
        self._create_income(
            amount='1000',
            month=1,
            category='cashless_20',
        )

        self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=1,
            deadline=date(2026, 2, 15),
        )

        february = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=2,
            deadline=date(2026, 3, 15),
        )

        self.assertEqual(
            february.field_17,
            Decimal('0.00'),
        )

        self.assertEqual(
            february.field_15,
            Decimal('1000.00'),
        )

        self.assertEqual(
            february.field_26,
            Decimal('0.00'),
        )

    def test_recalculate_future_periods_after_past_change(self):
        january_income = self._create_income(
            amount='1000',
            month=1,
            category='cashless_20',
        )

        self._create_income(
            amount='500',
            month=2,
            category='cashless_20',
        )

        self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=1,
            deadline=date(2026, 2, 15),
        )

        self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=2,
            deadline=date(2026, 3, 15),
        )

        february = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=2,
        )

        self.assertEqual(
            february.field_15,
            Decimal('1500.00'),
        )

        january_income.amount_gel = Decimal('2000.00')
        january_income.save(update_fields=['amount_gel'])

        self.service.recalculate_from_month(
            user=self.user,
            year=2026,
            month=1,
        )

        january = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=1,
        )

        february.refresh_from_db()

        self.assertEqual(
            january.field_17,
            Decimal('2000.00'),
        )

        self.assertEqual(
            january.field_15,
            Decimal('2000.00'),
        )

        self.assertEqual(
            february.field_17,
            Decimal('500.00'),
        )

        self.assertEqual(
            february.field_15,
            Decimal('2500.00'),
        )

    def test_change_after_submission_sets_flag(self):
        income = self._create_income(
            amount='1000',
            month=8,
            category='cashless_20',
        )

        period = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
            deadline=date(2026, 9, 15),
        )

        period.declaration_status = 'submitted'
        period.save(update_fields=['declaration_status'])

        income.amount_gel = Decimal('1500.00')
        income.save(update_fields=['amount_gel'])

        self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        period.refresh_from_db()

        self.assertEqual(
            period.declaration_status,
            'submitted',
        )

        self.assertTrue(period.changed_after_submission)

        self.assertEqual(
            period.field_20,
            Decimal('1500.00'),
        )

    def test_deleted_income_is_not_counted(self):
        self._create_income(
            amount='1000',
            month=8,
            category='cashless_20',
        )

        self._create_income(
            amount='500',
            month=8,
            category='cashless_20',
            is_deleted=True,
        )

        period = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
            deadline=date(2026, 9, 15),
        )

        self.assertEqual(
            period.field_20,
            Decimal('1000.00'),
        )

        self.assertEqual(
            period.field_17,
            Decimal('1000.00'),
        )

    def test_invalid_month_raises_error(self):
        with self.assertRaises(ValidationError):
            self.service.recalculate_period(
                user=self.user,
                year=2026,
                month=13,
                deadline=date(2026, 9, 15),
            )
