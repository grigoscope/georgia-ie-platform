import uuid
from datetime import timedelta

import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from invoices.models import (
    Invoice,
    InvoiceShareLink,
)
from invoices.pdf import InvoicePDFService


class InvoiceDeliveryError(ValueError):
    pass


class TemporaryInvoiceDeliveryError(
    InvoiceDeliveryError,
):
    pass


class PermanentInvoiceDeliveryError(
    InvoiceDeliveryError,
):
    pass


class InvoiceDeliveryService:
    def ensure_pdf(self, invoice):
        if not invoice.pdf_file:
            InvoicePDFService().generate(
                invoice=invoice,
            )
            invoice.refresh_from_db()

        return invoice

    def pdf_bytes(self, invoice):
        invoice = self.ensure_pdf(
            invoice,
        )

        invoice.pdf_file.open('rb')

        try:
            return invoice.pdf_file.read()

        finally:
            invoice.pdf_file.close()

    def send_to_telegram(
        self,
        *,
        invoice,
        connection,
    ):
        if invoice.status == 'cancelled':
            raise (
                PermanentInvoiceDeliveryError(
                    'Отменённый инвойс нельзя отправить.'
                )
            )

        if not connection.is_active:
            raise (
                PermanentInvoiceDeliveryError(
                    'Telegram не подключён.'
                )
            )

        if invoice.telegram_sent_at:
            return {
                'ok': True,
                'already_sent': True,
                'result': {
                    'message_id':
                        invoice.telegram_message_id,
                },
            }

        bot_token = (
            settings.TELEGRAM_BOT_TOKEN
        )

        if not bot_token:
            raise (
                PermanentInvoiceDeliveryError(
                    'Telegram Bot Token не настроен.'
                )
            )

        pdf = self.pdf_bytes(
            invoice,
        )

        url = (
            f'https://api.telegram.org/'
            f'bot{bot_token}/sendDocument'
        )

        try:
            response = requests.post(
                url,
                data={
                    'chat_id':
                        connection.telegram_chat_id,
                    'caption':
                        f'Invoice {invoice.number}',
                },
                files={
                    'document': (
                        f'invoice-{invoice.number}.pdf',
                        pdf,
                        'application/pdf',
                    )
                },
                timeout=20,
            )

            response.raise_for_status()

            payload = response.json()

        except requests.Timeout as error:
            raise (
                TemporaryInvoiceDeliveryError(
                    'Telegram временно недоступен.'
                )
            ) from error

        except requests.ConnectionError as error:
            raise (
                TemporaryInvoiceDeliveryError(
                    'Не удалось подключиться к Telegram.'
                )
            ) from error

        except requests.HTTPError as error:
            status_code = (
                error.response.status_code
                if error.response is not None
                else None
            )

            if (
                status_code == 429
                or (
                    status_code is not None
                    and status_code >= 500
                )
            ):
                raise (
                    TemporaryInvoiceDeliveryError(
                        'Telegram временно отклонил отправку.'
                    )
                ) from error

            raise (
                PermanentInvoiceDeliveryError(
                    'Telegram отклонил отправку инвойса.'
                )
            ) from error

        except requests.RequestException as error:
            raise (
                TemporaryInvoiceDeliveryError(
                    'Не удалось отправить инвойс в Telegram.'
                )
            ) from error

        except ValueError as error:
            raise (
                PermanentInvoiceDeliveryError(
                    'Telegram вернул некорректный ответ.'
                )
            ) from error

        if not payload.get('ok'):
            raise (
                PermanentInvoiceDeliveryError(
                    payload.get(
                        'description',
                        'Telegram отклонил отправку.',
                    )
                )
            )

        result = (
            payload.get('result')
            or {}
        )

        self._mark_telegram_sent(
            invoice=invoice,
            message_id=result.get(
                'message_id',
            ),
        )

        return payload

    def send_email(
        self,
        *,
        invoice,
        recipient,
    ):
        if invoice.status == 'cancelled':
            raise InvoiceDeliveryError(
                'Отменённый инвойс нельзя отправить.'
            )

        pdf = self.pdf_bytes(
            invoice,
        )

        email = EmailMessage(
            subject=f'Invoice {invoice.number}',
            body=(
                f'Invoice {invoice.number} '
                f'is attached.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )

        email.attach(
            f'invoice-{invoice.number}.pdf',
            pdf,
            'application/pdf',
        )

        try:
            email.send(
                fail_silently=False,
            )

        except Exception as error:
            raise InvoiceDeliveryError(
                'Не удалось отправить инвойс по email.'
            ) from error

        self._mark_sent(
            invoice,
        )

    @staticmethod
    def _mark_sent(invoice):
        invoice.refresh_from_db()

        update_fields = [
            'sent_at',
            'updated_at',
        ]

        invoice.sent_at = timezone.now()

        if invoice.status == 'draft':
            invoice.status = 'pending'
            update_fields.append(
                'status',
            )

        invoice.save(
            update_fields=update_fields,
        )

    @staticmethod
    def _mark_telegram_sent(
        *,
        invoice,
        message_id,
    ):
        invoice.refresh_from_db()

        update_fields = [
            'sent_at',
            'telegram_sent_at',
            'telegram_message_id',
            'updated_at',
        ]

        now = timezone.now()

        invoice.sent_at = now
        invoice.telegram_sent_at = now
        invoice.telegram_message_id = (
            message_id
        )

        if invoice.status == 'draft':
            invoice.status = 'pending'
            update_fields.append(
                'status',
            )

        invoice.save(
            update_fields=update_fields,
        )


class InvoiceShareLinkService:
    @transaction.atomic
    def create(
        self,
        *,
        invoice,
        expires_in_hours,
    ):
        invoice = (
            Invoice.objects
            .select_for_update()
            .get(pk=invoice.pk)
        )

        InvoicePDFService().generate(
            invoice=invoice,
        )

        expires_at = (
            timezone.now()
            + timedelta(
                hours=expires_in_hours,
            )
        )

        link, _ = (
            InvoiceShareLink.objects
            .get_or_create(
                invoice=invoice,
                defaults={
                    'expires_at':
                        expires_at,
                },
            )
        )

        link.token = uuid.uuid4()
        link.expires_at = expires_at
        link.revoked_at = None

        link.save()

        return link

    @transaction.atomic
    def revoke(
        self,
        *,
        invoice,
    ):
        link = (
            InvoiceShareLink.objects
            .select_for_update()
            .filter(invoice=invoice)
            .first()
        )

        if link:
            link.revoked_at = (
                timezone.now()
            )

            link.save(
                update_fields=[
                    'revoked_at',
                    'updated_at',
                ],
            )

        return link
