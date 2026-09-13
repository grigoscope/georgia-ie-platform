from datetime import date

from celery import shared_task
from django.utils import timezone

from notifications.tax_reminders import TaxReminderService


@shared_task(
    name='notifications.celery_healthcheck',
)
def celery_healthcheck():
    return {
        'status': 'ok',
        'checked_at': timezone.now().isoformat(),
    }


@shared_task(
    name='notifications.run_daily_tax_cycle',
)
def run_daily_tax_cycle(
    for_date=None,
):
    parsed_date = None

    if for_date:
        parsed_date = date.fromisoformat(
            for_date,
        )

    return TaxReminderService.run(
        for_date=parsed_date,
    )
