from datetime import date

from celery import shared_task
from django.utils import timezone

from notifications.delivery import (
    NotificationDeliveryService,
    PermanentTelegramDeliveryError,
    TemporaryTelegramDeliveryError,
)
from notifications.models import Notification
from notifications.tax_reminders import (
    TaxReminderService,
)


@shared_task(
    name='notifications.celery_healthcheck',
)
def celery_healthcheck():
    return {
        'status': 'ok',
        'checked_at':
            timezone.now().isoformat(),
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


@shared_task(
    bind=True,
    name='notifications.deliver_telegram_notification',
    max_retries=3,
)
def deliver_telegram_notification(
    self,
    notification_id,
):
    try:
        return (
            NotificationDeliveryService
            .deliver_telegram(
                notification_id=
                    notification_id,
            )
        )

    except TemporaryTelegramDeliveryError as error:
        countdown = min(
            30 * (2 ** self.request.retries),
            300,
        )

        raise self.retry(
            exc=error,
            countdown=countdown,
        )

    except PermanentTelegramDeliveryError as error:
        return {
            'status': 'failed',
            'notification_id':
                notification_id,
            'error': str(error),
        }


@shared_task(
    name='notifications.dispatch_pending_telegram',
)
def dispatch_pending_telegram():
    notification_ids = list(
        Notification.objects
        .filter(
            telegram_sent_at__isnull=True,
            delivery_status__in=[
                'pending',
                'retrying',
            ],
            user__is_active=True,
            user__notification_settings__telegram_enabled=True,
            user__telegram_connection__is_active=True,
        )
        .values_list(
            'id',
            flat=True,
        )[:500]
    )

    for notification_id in notification_ids:
        deliver_telegram_notification.delay(
            notification_id,
        )

    return {
        'queued': len(
            notification_ids
        ),
    }