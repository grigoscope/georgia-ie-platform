from celery import shared_task

from exchange_rates.models import Currency
from exchange_rates.services import (
    ExchangeRateService,
    NBGRateError,
)


@shared_task(
    bind=True,
    name='exchange_rates.update_official_rates',
    max_retries=3,
)
def update_official_rates(self):
    service = ExchangeRateService()

    currency_codes = list(
        Currency.objects
        .filter(
            is_active=True,
            kind='fiat',
        )
        .order_by('code')
        .values_list(
            'code',
            flat=True,
        )
    )

    updated = []

    try:
        for currency_code in currency_codes:
            rate = service.get_current_rate(
                currency_code,
            )

            updated.append(
                {
                    'currency': currency_code,
                    'rate_id': rate.pk,
                    'rate_date': (
                        rate.rate_date.isoformat()
                    ),
                    'source': rate.source,
                }
            )

    except NBGRateError as error:
        countdown = min(
            60 * (
                2 ** self.request.retries
            ),
            900,
        )

        raise self.retry(
            exc=error,
            countdown=countdown,
        )

    return {
        'processed': len(updated),
        'currencies': updated,
    }
