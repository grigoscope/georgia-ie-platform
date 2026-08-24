from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import FinancialAccount
from incomes.models import IncomeEntry
from taxes.services import (
    TaxPeriodCalculationService,
)

User = get_user_model()


class TaxPeriodTimezoneTests(TestCase):
    """Границы месяца определяются по Asia/Tbilisi."""

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
        received_at,
        amount,
    ):
        return IncomeEntry.objects.create(
            user=self.user,
            received_at=received_at,
            description='Boundary income',
            financial_account=self.account,
            original_amount=Decimal(amount),
            original_currency=self.gel,
            exchange_rate_value=Decimal('1'),
            exchange_rate_unit=1,
            exchange_rate_source='GEL',
            exchange_rate_date=(received_at.date()),
            amount_gel=Decimal(amount),
            declaration_category='cashless_20',
        )

    def test_utc_august_but_tbilisi_september(
        self,
    ):
        """
        31 Aug 21:30 UTC
        =
        1 Sep 01:30 Tbilisi.
        """

        received_at = datetime(
            2026,
            8,
            31,
            21,
            30,
            tzinfo=ZoneInfo('UTC'),
        )

        self._create_income(
            received_at=received_at,
            amount='100.00',
        )

        august = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        september = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=9,
        )

        self.assertEqual(
            august.field_17,
            Decimal('0.00'),
        )

        self.assertEqual(
            september.field_17,
            Decimal('100.00'),
        )

    def test_exact_start_of_tbilisi_month(
        self,
    ):
        """
        1 Sep 00:00 Tbilisi
        =
        31 Aug 20:00 UTC.
        """

        tbilisi = ZoneInfo('Asia/Tbilisi')

        received_at = datetime(
            2026,
            9,
            1,
            0,
            0,
            tzinfo=tbilisi,
        )

        self._create_income(
            received_at=received_at,
            amount='250.00',
        )

        september = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=9,
        )

        self.assertEqual(
            september.field_20,
            Decimal('250.00'),
        )

    def test_last_second_of_tbilisi_month(
        self,
    ):
        tbilisi = ZoneInfo('Asia/Tbilisi')

        received_at = datetime(
            2026,
            8,
            31,
            23,
            59,
            59,
            tzinfo=tbilisi,
        )

        self._create_income(
            received_at=received_at,
            amount='300.00',
        )

        august = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        september = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=9,
        )

        self.assertEqual(
            august.field_17,
            Decimal('300.00'),
        )

        self.assertEqual(
            september.field_17,
            Decimal('0.00'),
        )
