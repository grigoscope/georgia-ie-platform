from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from audit.admin_utils import (
    AdminAuditMixin,
    DangerousAdminMixin,
    NoBulkDeleteAdminMixin,
)
from invoices.delivery_services import (
    InvoiceDeliveryError,
    InvoiceDeliveryService,
)
from invoices.models import (
    Invoice,
    InvoiceItem,
    InvoicePayment,
    InvoiceShareLink,
)
from invoices.pdf import InvoicePDFService


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    can_delete = False

    fields = (
        'position',
        'description',
        'quantity',
        'unit',
        'unit_price',
        'line_total',
    )

    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0
    can_delete = False

    fields = (
        'amount',
        'currency',
        'paid_at',
        'income_entry',
        'created_at',
    )

    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(
    NoBulkDeleteAdminMixin,
    DangerousAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    list_display = (
        'number',
        'user',
        'counterparty',
        'total_display',
        'status',
        'issue_date',
        'due_date',
        'pdf_status',
    )

    list_filter = (
        'status',
        'currency',
        'language',
        'issue_date',
        'due_date',
    )

    search_fields = (
        'number',
        'user__email',
        'counterparty__name',
    )

    date_hierarchy = 'issue_date'
    ordering = ('-issue_date', '-id')
    list_select_related = ('user', 'counterparty', 'currency')
    autocomplete_fields = ('user', 'counterparty', 'currency')

    readonly_fields = (
        'number',
        'seller_snapshot',
        'buyer_snapshot',
        'payment_details_snapshot',
        'subtotal',
        'total_amount',
        'pdf_checksum',
        'generated_at',
        'sent_at',
        'paid_at',
        'cancelled_at',
        'created_at',
        'updated_at',
    )

    inlines = (
        InvoiceItemInline,
        InvoicePaymentInline,
    )

    actions = (
        'regenerate_pdf',
        'send_to_owner_telegram',
        'revoke_share_links',
    )

    @admin.display(description='Сумма', ordering='total_amount')
    def total_display(self, obj):
        return f'{obj.total_amount} {obj.currency.code}'

    @admin.display(description='PDF', boolean=True)
    def pdf_status(self, obj):
        return bool(obj.pdf_file and obj.generated_at)

    @admin.action(description='Повторно создать PDF')
    def regenerate_pdf(self, request, queryset):
        if not self.has_dangerous_permission(request):
            self.message_user(
                request,
                'Недостаточно прав для повторной генерации PDF.',
                level='ERROR',
            )
            return

        service = InvoicePDFService()
        generated = 0

        for invoice in queryset:
            old_checksum = invoice.pdf_checksum
            service.generate(invoice=invoice)
            invoice.refresh_from_db()

            self.write_admin_audit(
                request=request,
                obj=invoice,
                action='admin_regenerate_invoice_pdf',
                old_values={
                    'pdf_checksum': old_checksum,
                },
                new_values={
                    'pdf_checksum': invoice.pdf_checksum,
                    'generated_at': invoice.generated_at,
                },
            )
            generated += 1

        self.message_user(request, f'PDF создан повторно: {generated}.')

    @admin.action(description='Повторно отправить владельцу в Telegram')
    def send_to_owner_telegram(self, request, queryset):
        if not self.has_dangerous_permission(request):
            self.message_user(
                request,
                'Недостаточно прав для отправки инвойсов.',
                level='ERROR',
            )
            return

        service = InvoiceDeliveryService()
        sent = 0
        failed = 0

        for invoice in queryset.select_related('user'):
            try:
                connection = invoice.user.telegram_connection

                old_values = {
                    'status': invoice.status,
                    'sent_at': invoice.sent_at,
                }

                payload = service.send_to_telegram(
                    invoice=invoice,
                    connection=connection,
                )

                invoice.refresh_from_db()

                result = payload.get('result') or {}
                message_id = result.get('message_id')

                self.write_admin_audit(
                    request=request,
                    obj=invoice,
                    action='admin_resend_invoice_to_owner',
                    old_values=old_values,
                    new_values={
                        'status': invoice.status,
                        'sent_at': invoice.sent_at,
                        'telegram_message_id': message_id,
                    },
                )

                sent += 1

            except ObjectDoesNotExist:
                failed += 1

            except InvoiceDeliveryError:
                failed += 1

        self.message_user(
            request,
            f'Отправлено: {sent}. Ошибок: {failed}.',
        )

    @admin.action(description='Отозвать публичные ссылки')
    def revoke_share_links(self, request, queryset):
        if not self.has_dangerous_permission(request):
            self.message_user(
                request,
                'Недостаточно прав для отзыва ссылок.',
                level='ERROR',
            )
            return

        revoked = 0

        links = (
            InvoiceShareLink.objects
            .filter(
                invoice__in=queryset,
                revoked_at__isnull=True,
            )
            .select_related('invoice')
        )

        for link in links:
            link.revoked_at = timezone.now()
            link.save(
                update_fields=[
                    'revoked_at',
                    'updated_at',
                ],
            )

            self.write_admin_audit(
                request=request,
                obj=link.invoice,
                action='admin_revoke_invoice_share_link',
                new_values={
                    'share_link_id': link.pk,
                    'revoked_at': link.revoked_at,
                },
            )
            revoked += 1

        self.message_user(request, f'Отозвано ссылок: {revoked}.')

    def has_delete_permission(self, request, obj=None):
        return self.has_dangerous_permission(request)


@admin.register(InvoiceShareLink)
class InvoiceShareLinkAdmin(
    NoBulkDeleteAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        'invoice',
        'expires_at',
        'revoked_at',
        'created_at',
    )

    list_filter = (
        'expires_at',
        'revoked_at',
    )

    search_fields = (
        'invoice__number',
        'invoice__user__email',
    )

    readonly_fields = (
        'invoice',
        'token',
        'expires_at',
        'revoked_at',
        'created_at',
        'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
