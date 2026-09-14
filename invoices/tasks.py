from celery import shared_task
from django.utils import timezone

from invoices.delivery_services import (
    InvoiceDeliveryService,
    PermanentInvoiceDeliveryError,
    TemporaryInvoiceDeliveryError,
)
from invoices.models import (
    Invoice,
    InvoiceShareLink,
)
from invoices.pdf import (
    InvoicePDFService,
)
from telegram_integration.models import (
    TelegramConnection,
)


@shared_task(
    name='invoices.generate_invoice_pdf',
)
def generate_invoice_pdf(
    invoice_id,
):
    invoice = (
        Invoice.objects
        .select_related(
            'currency',
            'counterparty',
            'user',
        )
        .get(pk=invoice_id)
    )

    InvoicePDFService().generate(
        invoice=invoice,
    )

    return {
        'status': 'generated',
        'invoice_id': invoice.pk,
    }


@shared_task(
    bind=True,
    name='invoices.send_invoice_pdf_telegram',
    max_retries=3,
)
def send_invoice_pdf_telegram(
    self,
    invoice_id,
):
    invoice = (
        Invoice.objects
        .select_related('user')
        .get(pk=invoice_id)
    )

    if invoice.telegram_sent_at:
        return {
            'status': 'already_sent',
            'invoice_id': invoice.pk,
            'message_id':
                invoice.telegram_message_id,
        }

    connection = (
        TelegramConnection.objects
        .filter(
            user=invoice.user,
            is_active=True,
        )
        .first()
    )

    if connection is None:
        return {
            'status': 'skipped',
            'invoice_id': invoice.pk,
            'reason':
                'Telegram не подключён.',
        }

    try:
        payload = (
            InvoiceDeliveryService()
            .send_to_telegram(
                invoice=invoice,
                connection=connection,
            )
        )

    except TemporaryInvoiceDeliveryError as error:
        countdown = min(
            30 * (
                2 ** self.request.retries
            ),
            300,
        )

        raise self.retry(
            exc=error,
            countdown=countdown,
        )

    except PermanentInvoiceDeliveryError as error:
        return {
            'status': 'failed',
            'invoice_id': invoice.pk,
            'error': str(error),
        }

    result = (
        payload.get('result')
        or {}
    )

    return {
        'status': 'sent',
        'invoice_id': invoice.pk,
        'message_id':
            result.get('message_id'),
    }


@shared_task(
    name='invoices.cleanup_expired_share_links',
)
def cleanup_expired_share_links():
    now = timezone.now()

    queryset = (
        InvoiceShareLink.objects
        .filter(
            expires_at__lt=now,
        )
    )

    deleted, _ = queryset.delete()

    return {
        'deleted': deleted,
    }


@shared_task(
    name='invoices.mark_overdue_invoices',
)
def mark_overdue_invoices():
    today = timezone.localdate()

    overdue_qs = (
        Invoice.objects
        .filter(
            due_date__lt=today,
            status__in=[
                'pending',
                'partially_paid',
            ],
            is_overdue=False,
        )
    )

    marked = overdue_qs.update(
        is_overdue=True,
    )

    reset = (
        Invoice.objects
        .filter(
            is_overdue=True,
        )
        .exclude(
            due_date__lt=today,
            status__in=[
                'pending',
                'partially_paid',
            ],
        )
        .update(
            is_overdue=False,
        )
    )

    return {
        'marked_overdue': marked,
        'reset_overdue': reset,
    }
