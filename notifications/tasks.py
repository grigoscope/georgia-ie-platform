from celery import shared_task
from django.utils import timezone


@shared_task(
    name='notifications.celery_healthcheck',
)
def celery_healthcheck():
    return {
        'status': 'ok',
        'checked_at': (
            timezone.now().isoformat()
        ),
    }
