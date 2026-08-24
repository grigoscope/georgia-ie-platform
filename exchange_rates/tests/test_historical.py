from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from exchange_rates.models import (
    Currency,
    ExchangeRate,
)
from exchange_rates.services import (
    GELConversionService,
    NBGRateError,
)


class HistoricalRateTests(TestCase):
    """Тесты исторических курсов NBG."""

    @classmethod
    def setUpTestData(cls):
        cls.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            kind='fiat',
            decimal_places=2,
        )

        cls.jpy = Currency.objects.create(
            code='JPY',
            name='Japanese Yen',
            kind='fiat',
            decimal_places=2,
        )

    @patch('exchange_rates.services.NBGExchangeRateClient.get_current_rate')
    @patch('exchange_rates.services.NBGExchangeRateClient.get_rate_for_date')
    def test_historical_date_is_used(
        self,
        mock_historical,
        mock_current,
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
            'raw_reference': ('historical test'),
        }

        service = GELConversionService()

        result = service.convert(
            amount=Decimal('500'),
            currency_code='USD',
            rate_date=target_date,
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('1350.00'),
        )

        self.assertEqual(
            result['rate_value'],
            Decimal('2.70'),
        )

        self.assertEqual(
            result['rate_date'],
            target_date,
        )

        self.assertEqual(
            result['source'],
            'NBG',
        )

        mock_historical.assert_called_once_with(
            'USD',
            target_date,
        )

        mock_current.assert_not_called()

    @patch('exchange_rates.services.NBGExchangeRateClient.get_rate_for_date')
    def test_historical_rate_is_cached(
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
            'raw_reference': ('historical test'),
        }

        service = GELConversionService()

        service.convert(
            amount=Decimal('500'),
            currency_code='USD',
            rate_date=target_date,
        )

        service.convert(
            amount=Decimal('100'),
            currency_code='USD',
            rate_date=target_date,
        )

        self.assertEqual(
            mock_historical.call_count,
            1,
        )

        self.assertEqual(
            ExchangeRate.objects.filter(
                currency=self.usd,
                rate_date=target_date,
                source='NBG',
                is_manual=False,
            ).count(),
            1,
        )

    @patch('exchange_rates.services.NBGExchangeRateClient.get_rate_for_date')
    def test_historical_rate_respects_unit(
        self,
        mock_historical,
    ):
        target_date = date(
            2026,
            5,
            10,
        )

        mock_historical.return_value = {
            'currency_code': 'JPY',
            'rate_value': Decimal('1.60'),
            'rate_unit': 100,
            'rate_date': target_date,
            'rate_time': None,
            'source': 'NBG',
            'raw_reference': ('historical test'),
        }

        service = GELConversionService()

        result = service.convert(
            amount=Decimal('1000'),
            currency_code='JPY',
            rate_date=target_date,
        )

        self.assertEqual(
            result['rate_unit'],
            100,
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('16.00'),
        )

    @patch('exchange_rates.services.NBGExchangeRateClient.get_rate_for_date')
    def test_historical_nbg_error(
        self,
        mock_historical,
    ):
        mock_historical.side_effect = NBGRateError('NBG unavailable')

        service = GELConversionService()

        with self.assertRaises(NBGRateError):
            service.convert(
                amount=Decimal('500'),
                currency_code='USD',
                rate_date=date(
                    2026,
                    5,
                    10,
                ),
            )
