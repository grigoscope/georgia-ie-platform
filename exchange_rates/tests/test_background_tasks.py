from datetime import date
from decimal import Decimal
from unittest.mock import patch
from celery.exceptions import Retry

from django.test import TestCase

from exchange_rates.models import (
    Currency,
    ExchangeRate,
)
from exchange_rates.services import (
    ExchangeRateService,
    NBGRateError,
)
from exchange_rates.tasks import (
    update_official_rates,
)


class ExchangeRateBackgroundTaskTests(
    TestCase,
):
    def setUp(self):
        self.gel = Currency.objects.create(
            code='GEL',
            name='Georgian Lari',
            kind='fiat',
            is_active=True,
        )

        self.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            kind='fiat',
            is_active=True,
        )

        self.crypto = Currency.objects.create(
            code='BTC',
            name='Bitcoin',
            kind='crypto',
            is_active=True,
        )

    @patch(
        'exchange_rates.tasks.'
        'ExchangeRateService.get_current_rate'
    )
    def test_updates_only_active_fiat_currencies(
        self,
        get_current_rate,
    ):
        gel_rate = ExchangeRate.objects.create(
            currency=self.gel,
            rate_date=date(
                2026,
                9,
                14,
            ),
            rate_value=Decimal('1'),
            rate_unit=1,
            source='SYSTEM',
            is_manual=False,
        )

        usd_rate = ExchangeRate.objects.create(
            currency=self.usd,
            rate_date=date(
                2026,
                9,
                14,
            ),
            rate_value=Decimal('2.70'),
            rate_unit=1,
            source='NBG',
            is_manual=False,
        )

        def side_effect(
            currency_code,
        ):
            if currency_code == 'GEL':
                return gel_rate

            return usd_rate

        get_current_rate.side_effect = (
            side_effect
        )

        result = update_official_rates()

        called_codes = {
            call.args[0]
            for call in (
                get_current_rate.call_args_list
            )
        }

        self.assertEqual(
            called_codes,
            {
                'GEL',
                'USD',
            },
        )

        self.assertEqual(
            result['processed'],
            2,
        )

    @patch(
        'exchange_rates.tasks.'
        'ExchangeRateService.get_current_rate'
    )
    def test_nbg_error_requests_retry(
        self,
        get_current_rate,
    ):
        get_current_rate.side_effect = (
            NBGRateError(
                'NBG unavailable'
            )
        )

        with patch.object(
            update_official_rates,
            'retry',
            side_effect=Retry(),
        ) as retry:
            with self.assertRaises(
                Retry,
            ):
                update_official_rates.run()

        retry.assert_called_once()

        kwargs = retry.call_args.kwargs

        self.assertIsInstance(
            kwargs['exc'],
            NBGRateError,
        )

        self.assertEqual(
            kwargs['countdown'],
            60,
        )

    def test_manual_rate_is_not_overwritten(
        self,
    ):
        manual = (
            ExchangeRate.objects.create(
                currency=self.usd,
                rate_date=date(
                    2026,
                    9,
                    14,
                ),
                rate_value=Decimal(
                    '2.5000000000'
                ),
                rate_unit=1,
                source='manual',
                is_manual=True,
            )
        )

        service = (
            ExchangeRateService()
        )

        with patch.object(
            service.nbg_client,
            'get_rate_for_date',
            return_value={
                'currency_code': 'USD',
                'rate_value': Decimal(
                    '2.7000000000'
                ),
                'rate_unit': 1,
                'rate_date': date(
                    2026,
                    9,
                    14,
                ),
                'rate_time': None,
                'source': 'NBG',
                'raw_reference': 'test',
            },
        ):
            official = service.get_rate(
                'USD',
                rate_date=date(
                    2026,
                    9,
                    14,
                ),
            )

        manual.refresh_from_db()

        self.assertEqual(
            manual.rate_value,
            Decimal(
                '2.5000000000'
            ),
        )

        self.assertTrue(
            manual.is_manual,
        )

        self.assertFalse(
            official.is_manual,
        )

        self.assertEqual(
            official.source,
            'NBG',
        )

        self.assertNotEqual(
            official.pk,
            manual.pk,
        )

    def test_existing_official_rate_is_reused(
        self,
    ):
        existing = (
            ExchangeRate.objects.create(
                currency=self.usd,
                rate_date=date(
                    2026,
                    9,
                    14,
                ),
                rate_value=Decimal(
                    '2.7000000000'
                ),
                rate_unit=1,
                source='NBG',
                is_manual=False,
            )
        )

        service = (
            ExchangeRateService()
        )

        with patch.object(
            service.nbg_client,
            'get_rate_for_date',
        ) as get_rate:
            result = service.get_rate(
                'USD',
                rate_date=date(
                    2026,
                    9,
                    14,
                ),
            )

        self.assertEqual(
            result.pk,
            existing.pk,
        )

        get_rate.assert_not_called()
