from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from exchange_rates.models import Currency, ExchangeRate
from exchange_rates.services import (
    ExchangeRateService,
    GELConversionService,
    NBGRateError,
)


class ExchangeRateServiceTests(TestCase):
    """Тесты сервиса валютных курсов."""

    @classmethod
    def setUpTestData(cls):
        cls.gel = Currency.objects.create(
            code='GEL',
            name='Georgian Lari',
            kind='fiat',
            decimal_places=2,
        )

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

    @patch(
        'exchange_rates.services.'
        'NBGExchangeRateClient.get_current_rate'
    )
    def test_get_usd_rate_from_nbg(self, mock_get_rate):
        mock_get_rate.return_value = {
            'currency_code': 'USD',
            'rate_value': Decimal('2.7000'),
            'rate_unit': 1,
            'rate_date': date(2026, 8, 17),
            'rate_time': time(0, 0),
            'source': 'NBG',
        }

        service = ExchangeRateService()

        rate = service.get_current_rate('USD')

        self.assertEqual(
            rate.rate_value,
            Decimal('2.7000'),
        )
        self.assertEqual(rate.rate_unit, 1)
        self.assertEqual(rate.source, 'NBG')
        self.assertFalse(rate.is_manual)

    @patch(
        'exchange_rates.services.'
        'NBGExchangeRateClient.get_current_rate'
    )
    def test_rate_is_not_duplicated(self, mock_get_rate):
        mock_get_rate.return_value = {
            'currency_code': 'USD',
            'rate_value': Decimal('2.7000'),
            'rate_unit': 1,
            'rate_date': date(2026, 8, 17),
            'rate_time': time(0, 0),
            'source': 'NBG',
        }

        service = ExchangeRateService()

        service.get_current_rate('USD')
        service.get_current_rate('USD')

        self.assertEqual(
            ExchangeRate.objects.filter(
                currency=self.usd,
                source='NBG',
            ).count(),
            1,
        )

    @patch(
        'exchange_rates.services.'
        'NBGExchangeRateClient.get_current_rate'
    )
    def test_jpy_rate_unit(self, mock_get_rate):
        mock_get_rate.return_value = {
            'currency_code': 'JPY',
            'rate_value': Decimal('1.6437'),
            'rate_unit': 100,
            'rate_date': date(2026, 8, 17),
            'rate_time': time(0, 0),
            'source': 'NBG',
        }

        service = ExchangeRateService()

        rate = service.get_current_rate('JPY')

        self.assertEqual(rate.rate_unit, 100)
        self.assertEqual(
            rate.rate_value,
            Decimal('1.6437'),
        )

    def test_create_manual_rate(self):
        service = ExchangeRateService()

        rate = service.create_manual_rate(
            currency_code='USD',
            rate_value=Decimal('2.80'),
            rate_unit=1,
            source='manual_test',
        )

        self.assertEqual(
            rate.rate_value,
            Decimal('2.80'),
        )
        self.assertTrue(rate.is_manual)
        self.assertEqual(
            rate.source,
            'manual_test',
        )


class GELConversionServiceTests(TestCase):
    """Тесты конвертации в GEL."""

    @classmethod
    def setUpTestData(cls):
        Currency.objects.create(
            code='GEL',
            name='Georgian Lari',
            kind='fiat',
            decimal_places=2,
        )

        Currency.objects.create(
            code='USD',
            name='US Dollar',
            kind='fiat',
            decimal_places=2,
        )

        Currency.objects.create(
            code='JPY',
            name='Japanese Yen',
            kind='fiat',
            decimal_places=2,
        )

        Currency.objects.create(
            code='BTC',
            name='Bitcoin',
            kind='crypto',
            decimal_places=8,
        )

    def test_gel_without_conversion(self):
        service = GELConversionService()

        result = service.convert(
            Decimal('500'),
            'GEL',
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('500.00'),
        )
        self.assertEqual(
            result['rate_value'],
            Decimal('1'),
        )
        self.assertEqual(
            result['rate_unit'],
            1,
        )

    @patch(
        'exchange_rates.services.'
        'NBGExchangeRateClient.get_current_rate'
    )
    def test_usd_conversion(self, mock_get_rate):
        mock_get_rate.return_value = {
            'currency_code': 'USD',
            'rate_value': Decimal('2.70'),
            'rate_unit': 1,
            'rate_date': date(2026, 8, 17),
            'rate_time': time(0, 0),
            'source': 'NBG',
        }

        service = GELConversionService()

        result = service.convert(
            Decimal('500'),
            'USD',
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('1350.00'),
        )

    @patch(
        'exchange_rates.services.'
        'NBGExchangeRateClient.get_current_rate'
    )
    def test_rate_for_multiple_units(self, mock_get_rate):
        mock_get_rate.return_value = {
            'currency_code': 'JPY',
            'rate_value': Decimal('1.60'),
            'rate_unit': 100,
            'rate_date': date(2026, 8, 17),
            'rate_time': time(0, 0),
            'source': 'NBG',
        }

        service = GELConversionService()

        result = service.convert(
            Decimal('1000'),
            'JPY',
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('16.00'),
        )

    def test_manual_rate(self):
        service = GELConversionService()

        result = service.convert(
            amount=Decimal('500'),
            currency_code='USD',
            manual_rate_value=Decimal('2.70'),
            manual_source='user_manual',
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('1350.00'),
        )
        self.assertTrue(result['is_manual'])

        self.assertIn(
            'Использован ручной курс.',
            result['warnings'],
        )

    def test_ready_gel_equivalent(self):
        service = GELConversionService()

        result = service.convert(
            amount=Decimal('100'),
            currency_code='USD',
            ready_amount_gel=Decimal('270'),
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('270.00'),
        )

        self.assertEqual(
            result['rate_value'],
            Decimal('2.7000000000'),
        )

        self.assertEqual(
            result['source'],
            'provided_gel_equivalent',
        )

    def test_crypto_with_manual_rate(self):
        service = GELConversionService()

        result = service.convert(
            amount=Decimal('0.01'),
            currency_code='BTC',
            manual_rate_value=Decimal('180000'),
            manual_source='manual_crypto',
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('1800.00'),
        )

        self.assertTrue(result['is_manual'])

    def test_crypto_without_rate_raises_error(self):
        service = GELConversionService()

        with self.assertRaises(ValueError):
            service.convert(
                Decimal('0.01'),
                'BTC',
            )

    def test_ready_gel_for_crypto(self):
        service = GELConversionService()

        result = service.convert(
            amount=Decimal('0.01'),
            currency_code='BTC',
            ready_amount_gel=Decimal('1800'),
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('1800.00'),
        )

    @patch(
        'exchange_rates.services.'
        'NBGExchangeRateClient.get_current_rate'
    )
    def test_nbg_error(self, mock_get_rate):
        mock_get_rate.side_effect = NBGRateError(
            'NBG unavailable'
        )

        service = GELConversionService()

        with self.assertRaises(NBGRateError):
            service.convert(
                Decimal('500'),
                'USD',
            )

    @patch(
        'exchange_rates.services.'
        'NBGExchangeRateClient.get_current_rate'
    )
    def test_rounding(self, mock_get_rate):
        mock_get_rate.return_value = {
            'currency_code': 'USD',
            'rate_value': Decimal('2.675'),
            'rate_unit': 1,
            'rate_date': date(2026, 8, 17),
            'rate_time': time(0, 0),
            'source': 'NBG',
        }

        service = GELConversionService()

        result = service.convert(
            Decimal('1'),
            'USD',
        )

        self.assertEqual(
            result['amount_gel'],
            Decimal('2.68'),
        )