from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    EntrepreneurProfile,
)
from exchange_rates.models import (
    Currency,
    ExchangeRate,
)
from finances.models import (
    FinancialAccount,
)
from incomes.services import IncomeService

User = get_user_model()


class IncomeHistoricalRateTests(TestCase):
    """Исторический курс дохода замораживается."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Entrepreneur',
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
            default_declaration_category=('cashless_20'),
        )

    @patch('exchange_rates.services.NBGExchangeRateClient.get_rate_for_date')
    def test_income_freezes_historical_rate(
        self,
        mock_historical,
    ):
        target_date = date(
            2026,
            5,
            10,
        )

        mock_historical.return_value = {
            'currency_code': 'USD',
            'rate_value': Decimal('2.70'),
            'rate_unit': 1,
            'rate_date': target_date,
            'rate_time': None,
            'source': 'NBG',
            'raw_reference': ('historical acceptance'),
        }

        received_at = timezone.make_aware(
            datetime(
                2026,
                5,
                10,
                12,
                0,
            )
        )

        income = IncomeService().create_income(
            user=self.user,
            received_at=received_at,
            description='Historical USD income',
            financial_account=self.account,
            original_amount=(Decimal('500.00')),
            original_currency=self.usd,
            declaration_category=('cashless_20'),
            tax_period_deadline=date(
                2026,
                6,
                15,
            ),
        )

        self.assertEqual(
            income.exchange_rate_value,
            Decimal('2.7000000000'),
        )

        self.assertEqual(
            income.exchange_rate_unit,
            1,
        )

        self.assertEqual(
            income.exchange_rate_source,
            'NBG',
        )

        self.assertEqual(
            income.exchange_rate_date,
            target_date,
        )

        self.assertEqual(
            income.amount_gel,
            Decimal('1350.00'),
        )

        stored_rate = ExchangeRate.objects.get(
            currency=self.usd,
            rate_date=target_date,
            source='NBG',
        )

        stored_rate.rate_value = Decimal('9.99')

        stored_rate.save(
            update_fields=[
                'rate_value',
            ]
        )

        income.refresh_from_db()

        self.assertEqual(
            income.exchange_rate_value,
            Decimal('2.7000000000'),
        )

        self.assertEqual(
            income.amount_gel,
            Decimal('1350.00'),
        )
