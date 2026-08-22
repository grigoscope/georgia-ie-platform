from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from exchange_rates.models import Currency
from finances.models import Counterparty, FinancialAccount
from incomes.models import IncomeEntry
from incomes.reports import IncomeReportService
from taxes.models import TaxPeriod

User = get_user_model()


class IncomeReportServiceTests(TestCase):
    """Тесты отчётов по доходам."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpassword123',
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

        self.gel_account = FinancialAccount.objects.create(
            user=self.user,
            name='TBC GEL',
            type='bank_account',
            default_currency=self.gel,
        )

        self.usd_account = FinancialAccount.objects.create(
            user=self.user,
            name='TBC USD',
            type='bank_account',
            default_currency=self.usd,
        )

        self.other_account = FinancialAccount.objects.create(
            user=self.other_user,
            name='Other Account',
            type='bank_account',
            default_currency=self.gel,
        )

        self.counterparty_a = Counterparty.objects.create(
            user=self.user,
            name='Client A',
            type='company',
        )

        self.counterparty_b = Counterparty.objects.create(
            user=self.user,
            name='Client B',
            type='individual',
        )

        self.service = IncomeReportService()

    def _create_income(
        self,
        *,
        amount_gel,
        original_amount=None,
        currency=None,
        account=None,
        category='cashless_20',
        month=8,
        day=10,
        counterparty=None,
        user=None,
        is_deleted=False,
    ):
        user = user or self.user
        currency = currency or self.gel

        if account is None:
            if user == self.other_user:
                account = self.other_account
            else:
                account = self.gel_account

        if original_amount is None:
            original_amount = amount_gel

        received_at = timezone.make_aware(
            datetime(
                2026,
                month,
                day,
                12,
                0,
            )
        )

        rate_value = Decimal('1.0000000000') if currency.code == 'GEL' else Decimal('2.7000000000')

        return IncomeEntry.objects.create(
            user=user,
            received_at=received_at,
            description='Test income',
            counterparty=counterparty,
            financial_account=account,
            original_amount=Decimal(str(original_amount)),
            original_currency=currency,
            exchange_rate_value=rate_value,
            exchange_rate_unit=1,
            exchange_rate_source='test',
            exchange_rate_date=received_at.date(),
            amount_gel=Decimal(str(amount_gel)),
            declaration_category=category,
            is_deleted=is_deleted,
        )

    def test_monthly_report(self):
        self._create_income(
            amount_gel='100',
            category='cash_register_18',
        )

        self._create_income(
            amount_gel='200',
            category='physical_pos_19',
        )

        self._create_income(
            amount_gel='300',
            category='cashless_20',
        )

        self._create_income(
            amount_gel='400',
            category='other_21',
        )

        report = self.service.monthly(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            report['total_gel'],
            Decimal('1000.00'),
        )

        self.assertEqual(
            report['count'],
            4,
        )

        self.assertEqual(
            report['categories']['cash_register_18']['total_gel'],
            Decimal('100.00'),
        )

        self.assertEqual(
            report['categories']['physical_pos_19']['total_gel'],
            Decimal('200.00'),
        )

        self.assertEqual(
            report['categories']['cashless_20']['total_gel'],
            Decimal('300.00'),
        )

        self.assertEqual(
            report['categories']['other_21']['total_gel'],
            Decimal('400.00'),
        )

    def test_yearly_report(self):
        self._create_income(
            amount_gel='1000',
            month=1,
        )

        self._create_income(
            amount_gel='500',
            month=2,
        )

        self._create_income(
            amount_gel='250',
            month=8,
        )

        report = self.service.yearly(
            user=self.user,
            year=2026,
        )

        self.assertEqual(
            report['total_gel'],
            Decimal('1750.00'),
        )

        self.assertEqual(
            report['count'],
            3,
        )

        january = report['months'][0]
        february = report['months'][1]
        march = report['months'][2]
        august = report['months'][7]

        self.assertEqual(
            january['total_gel'],
            Decimal('1000.00'),
        )

        self.assertEqual(
            february['total_gel'],
            Decimal('500.00'),
        )

        self.assertEqual(
            march['total_gel'],
            Decimal('0.00'),
        )

        self.assertEqual(
            august['total_gel'],
            Decimal('250.00'),
        )

    def test_report_by_accounts(self):
        self._create_income(
            amount_gel='1000',
            account=self.gel_account,
        )

        self._create_income(
            amount_gel='270',
            original_amount='100',
            currency=self.usd,
            account=self.usd_account,
        )

        self._create_income(
            amount_gel='540',
            original_amount='200',
            currency=self.usd,
            account=self.usd_account,
        )

        report = self.service.by_accounts(
            user=self.user,
            year=2026,
            month=8,
        )

        data = {row['account_name']: row for row in report}

        self.assertEqual(
            data['TBC GEL']['total_gel'],
            Decimal('1000.00'),
        )

        self.assertEqual(
            data['TBC GEL']['count'],
            1,
        )

        self.assertEqual(
            data['TBC USD']['total_gel'],
            Decimal('810.00'),
        )

        self.assertEqual(
            data['TBC USD']['count'],
            2,
        )

    def test_report_by_currencies(self):
        self._create_income(
            amount_gel='500',
            original_amount='500',
            currency=self.gel,
            account=self.gel_account,
        )

        self._create_income(
            amount_gel='270',
            original_amount='100',
            currency=self.usd,
            account=self.usd_account,
        )

        self._create_income(
            amount_gel='540',
            original_amount='200',
            currency=self.usd,
            account=self.usd_account,
        )

        report = self.service.by_currencies(
            user=self.user,
            year=2026,
            month=8,
        )

        data = {row['currency_code']: row for row in report}

        self.assertEqual(
            data['GEL']['original_amount'],
            Decimal('500'),
        )

        self.assertEqual(
            data['GEL']['total_gel'],
            Decimal('500.00'),
        )

        self.assertEqual(
            data['USD']['original_amount'],
            Decimal('300'),
        )

        self.assertEqual(
            data['USD']['total_gel'],
            Decimal('810.00'),
        )

        self.assertEqual(
            data['USD']['count'],
            2,
        )

    def test_report_by_counterparties(self):
        self._create_income(
            amount_gel='100',
            counterparty=self.counterparty_a,
        )

        self._create_income(
            amount_gel='200',
            counterparty=self.counterparty_a,
        )

        self._create_income(
            amount_gel='300',
            counterparty=self.counterparty_b,
        )

        self._create_income(
            amount_gel='50',
            counterparty=None,
        )

        report = self.service.by_counterparties(
            user=self.user,
            year=2026,
            month=8,
        )

        data = {row['counterparty_name']: row for row in report}

        self.assertEqual(
            data['Client A']['total_gel'],
            Decimal('300.00'),
        )

        self.assertEqual(
            data['Client A']['count'],
            2,
        )

        self.assertEqual(
            data['Client B']['total_gel'],
            Decimal('300.00'),
        )

        self.assertEqual(
            data['Без контрагента']['total_gel'],
            Decimal('50.00'),
        )

    def test_report_by_categories_includes_zero_categories(self):
        self._create_income(
            amount_gel='700',
            category='cashless_20',
        )

        report = self.service.by_categories(
            user=self.user,
            year=2026,
            month=8,
        )

        data = {row['category']: row for row in report}

        self.assertEqual(
            data['cash_register_18']['total_gel'],
            Decimal('0.00'),
        )

        self.assertEqual(
            data['physical_pos_19']['total_gel'],
            Decimal('0.00'),
        )

        self.assertEqual(
            data['cashless_20']['total_gel'],
            Decimal('700.00'),
        )

        self.assertEqual(
            data['other_21']['total_gel'],
            Decimal('0.00'),
        )

    def test_deleted_and_foreign_incomes_are_ignored(self):
        self._create_income(
            amount_gel='1000',
        )

        self._create_income(
            amount_gel='500',
            is_deleted=True,
        )

        self._create_income(
            amount_gel='9999',
            user=self.other_user,
        )

        report = self.service.monthly(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            report['total_gel'],
            Decimal('1000.00'),
        )

        self.assertEqual(
            report['count'],
            1,
        )

    def test_monthly_report_matches_tax_period(self):
        self._create_income(
            amount_gel='1350',
            category='cashless_20',
        )

        TaxPeriod.objects.create(
            user=self.user,
            year=2026,
            month=8,
            field_20=Decimal('1350.00'),
            field_17=Decimal('1350.00'),
            field_15=Decimal('1350.00'),
            field_26=Decimal('13.50'),
            tax_rate=Decimal('1.00'),
            deadline=date(2026, 9, 15),
        )

        report = self.service.monthly(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertTrue(report['matches_tax_period'])

        self.assertEqual(
            report['tax_period']['field_17'],
            Decimal('1350.00'),
        )

    @patch(
        'incomes.reports.timezone.localdate',
        return_value=date(2026, 8, 22),
    )
    def test_dashboard(self, mocked_localdate):
        self._create_income(
            amount_gel='100',
            month=7,
        )

        self._create_income(
            amount_gel='200',
            month=8,
            day=1,
        )

        self._create_income(
            amount_gel='300',
            month=8,
            day=20,
        )

        report = self.service.dashboard(user=self.user)

        self.assertEqual(
            report['current_month']['total_gel'],
            Decimal('500.00'),
        )

        self.assertEqual(
            report['current_year']['total_gel'],
            Decimal('600.00'),
        )

        self.assertEqual(
            report['current_year']['count'],
            3,
        )

        self.assertEqual(
            len(report['recent_incomes']),
            3,
        )

        self.assertEqual(
            report['recent_incomes'][0]['amount_gel'],
            Decimal('300'),
        )
