from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from exchange_rates.models import (
    Currency,
    ExchangeRate,
)

User = get_user_model()


class ExchangeRateAPITests(APITestCase):
    """API валют и курсов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
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

        self.btc = Currency.objects.create(
            code='BTC',
            name='Bitcoin',
            kind='crypto',
            decimal_places=8,
        )

        self.inactive = Currency.objects.create(
            code='OLD',
            name='Inactive currency',
            kind='fiat',
            decimal_places=2,
            is_active=False,
        )

        self.client.force_authenticate(user=self.user)

    def test_currencies_require_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse('currency-list'))

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_currency_list_contains_only_active(
        self,
    ):
        response = self.client.get(reverse('currency-list'))

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        codes = {item['code'] for item in response.data}

        self.assertIn(
            'GEL',
            codes,
        )

        self.assertIn(
            'USD',
            codes,
        )

        self.assertIn(
            'BTC',
            codes,
        )

        self.assertNotIn(
            'OLD',
            codes,
        )

    def test_get_cached_historical_rate(
        self,
    ):
        ExchangeRate.objects.create(
            currency=self.usd,
            rate_date=date(
                2026,
                3,
                30,
            ),
            rate_value=Decimal('2.7000000000'),
            rate_unit=1,
            source='NBG',
            is_manual=False,
        )

        response = self.client.get(
            reverse('exchange-rate'),
            {
                'currency': 'USD',
                'date': '2026-03-30',
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['currency'],
            'USD',
        )

        self.assertEqual(
            Decimal(response.data['rate_value']),
            Decimal('2.7000000000'),
        )

        self.assertEqual(
            response.data['rate_unit'],
            1,
        )

    def test_convert_gel(self):
        response = self.client.post(
            reverse('exchange-rate-convert'),
            {
                'amount': '310.00',
                'currency': 'GEL',
                'date': '2026-08-25',
                'mode': 'automatic',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.data['data']

        self.assertEqual(
            data['currency'],
            'GEL',
        )

        self.assertEqual(
            data['amount_gel'],
            '310.00',
        )

        self.assertEqual(
            Decimal(data['rate_value']),
            Decimal('1'),
        )

    def test_convert_usd_using_cached_rate(
        self,
    ):
        ExchangeRate.objects.create(
            currency=self.usd,
            rate_date=date(
                2026,
                3,
                30,
            ),
            rate_value=Decimal('2.7000000000'),
            rate_unit=1,
            source='NBG',
            is_manual=False,
        )

        response = self.client.post(
            reverse('exchange-rate-convert'),
            {
                'amount': '500.00',
                'currency': 'USD',
                'date': '2026-03-30',
                'mode': 'automatic',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.data['data']

        self.assertEqual(
            data['amount_gel'],
            '1350.00',
        )

        self.assertEqual(
            data['source'],
            'NBG',
        )

        self.assertFalse(data['is_manual'])

    def test_manual_conversion(self):
        response = self.client.post(
            reverse('exchange-rate-convert'),
            {
                'amount': '500.00',
                'currency': 'USD',
                'date': '2026-03-30',
                'mode': 'manual',
                'rate_value': '2.7000000000',
                'rate_unit': 1,
                'source': 'manual-test',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.data['data']

        self.assertEqual(
            data['amount_gel'],
            '1350.00',
        )

        self.assertTrue(data['is_manual'])

        self.assertEqual(
            data['source'],
            'manual-test',
        )

    def test_manual_mode_requires_rate(
        self,
    ):
        response = self.client.post(
            reverse('exchange-rate-convert'),
            {
                'amount': '500.00',
                'currency': 'USD',
                'mode': 'manual',
                'source': 'manual',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_ready_gel_conversion(self):
        response = self.client.post(
            reverse('exchange-rate-convert'),
            {
                'amount': '100.00',
                'currency': 'USD',
                'mode': 'ready_gel',
                'amount_gel': '275.00',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['data']['amount_gel'],
            '275.00',
        )

    def test_crypto_estimate_by_rate(
        self,
    ):
        response = self.client.post(
            reverse('exchange-rate-crypto-estimate'),
            {
                'asset': 'BTC',
                'amount': '0.0100000000',
                'rate': '170000.0000000000',
                'rate_unit': 1,
                'source': 'manual-market',
                'valued_at': ('2026-08-25T12:00:00Z'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.data['data']

        self.assertEqual(
            data['asset'],
            'BTC',
        )

        self.assertEqual(
            data['amount_gel'],
            '1700.00',
        )

        self.assertTrue(data['is_manual'])

    def test_crypto_estimate_by_ready_gel(
        self,
    ):
        response = self.client.post(
            reverse('exchange-rate-crypto-estimate'),
            {
                'asset': 'BTC',
                'amount': '0.0100000000',
                'amount_gel': '1800.00',
                'source': 'exchange-snapshot',
                'valued_at': ('2026-08-25T12:00:00Z'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['data']['amount_gel'],
            '1800.00',
        )

    def test_crypto_requires_rate_or_gel(
        self,
    ):
        response = self.client.post(
            reverse('exchange-rate-crypto-estimate'),
            {
                'asset': 'BTC',
                'amount': '0.0100000000',
                'source': 'manual',
                'valued_at': ('2026-08-25T12:00:00Z'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_fiat_is_rejected_by_crypto_endpoint(
        self,
    ):
        response = self.client.post(
            reverse('exchange-rate-crypto-estimate'),
            {
                'asset': 'USD',
                'amount': '10.00',
                'rate': '2.70',
                'source': 'manual',
                'valued_at': ('2026-08-25T12:00:00Z'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
