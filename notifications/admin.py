from django.contrib import admin
from django.utils import timezone

from audit.admin_utils import (
    AdminAuditMixin,
    DangerousAdminMixin,
    NoBulkDeleteAdminMixin,
)
from notifications.models import (
    Notification,
    NotificationSettings,
)
from telegram_integration.bot import (
    TelegramBotClient,
)


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(
    NoBulkDeleteAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    list_display = (
        'user',
        'internal_enabled',
        'telegram_enabled',
        'email_enabled',
        'tax_reminders_enabled',
        'invoice_reminders_enabled',
        'send_time',
    )

    list_filter = (
        'internal_enabled',
        'telegram_enabled',
        'email_enabled',
        'tax_reminders_enabled',
        'invoice_reminders_enabled',
    )

    search_fields = (
        'user__email',
    )

    autocomplete_fields = (
        'user',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )


@admin.register(Notification)
class NotificationAdmin(
    NoBulkDeleteAdminMixin,
    DangerousAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    list_display = (
        'created_at',
        'type',
        'user',
        'title',
        'delivery_status',
        'scheduled_for',
        'telegram_sent_at',
        'email_sent_at',
        'error_preview',
    )

    list_filter = (
        'type',
        'delivery_status',
        'created_at',
        'scheduled_for',
        'telegram_sent_at',
        'email_sent_at',
    )

    search_fields = (
        'user__email',
        'title',
        'message',
        'deduplication_key',
        'error_message',
    )

    ordering = (
        '-created_at',
    )

    list_select_related = (
        'user',
    )

    readonly_fields = (
        'created_at',
        'delivery_status',
        'telegram_sent_at',
        'email_sent_at',
        'error_message',
    )

    autocomplete_fields = (
        'user',
    )

    actions = (
        'retry_telegram_delivery',
        'cancel_pending',
    )

    @admin.display(
        description='Ошибка',
    )
    def error_preview(
        self,
        obj,
    ):
        if not obj.error_message:
            return ''

        if len(
            obj.error_message
        ) <= 80:
            return obj.error_message

        return (
            obj.error_message[:77]
            + '...'
        )

    @admin.action(
        description='Повторить отправку в Telegram',
    )
    def retry_telegram_delivery(
        self,
        request,
        queryset,
    ):
        if not self.has_dangerous_permission(
            request,
        ):
            self.message_user(
                request,
                'Недостаточно прав для повторной отправки.',
                level='ERROR',
            )
            return

        client = TelegramBotClient()
        sent = 0
        failed = 0

        for notification in queryset:
            try:
                connection = (
                    notification.user
                    .telegram_connection
                )

                if not connection.is_active:
                    raise RuntimeError(
                        'Telegram-связь отключена.'
                    )

                client.send_message(
                    chat_id=(
                        connection
                        .telegram_chat_id
                    ),
                    text=(
                        f'{notification.title}\n\n'
                        f'{notification.message}'
                    ),
                )

                old_values = {
                    'delivery_status':
                        notification
                        .delivery_status,
                    'error_message':
                        notification
                        .error_message,
                }

                notification.delivery_status = (
                    'sent'
                )

                notification.telegram_sent_at = (
                    timezone.now()
                )

                notification.error_message = ''

                notification.save(
                    update_fields=[
                        'delivery_status',
                        'telegram_sent_at',
                        'error_message',
                    ],
                )

                self.write_admin_audit(
                    request=request,
                    obj=notification,
                    action='admin_retry_telegram_notification',
                    old_values=old_values,
                    new_values={
                        'delivery_status':
                            'sent',
                        'telegram_sent_at':
                            notification
                            .telegram_sent_at,
                    },
                )

                sent += 1

            except Exception as error:
                notification.delivery_status = (
                    'failed'
                )

                notification.error_message = (
                    str(error)[:2000]
                )

                notification.save(
                    update_fields=[
                        'delivery_status',
                        'error_message',
                    ],
                )

                failed += 1

        self.message_user(
            request,
            (
                f'Отправлено: {sent}. '
                f'Ошибок: {failed}.'
            ),
        )

    @admin.action(
        description='Отменить неотправленные уведомления',
    )
    def cancel_pending(
        self,
        request,
        queryset,
    ):
        if not self.has_dangerous_permission(
            request,
        ):
            self.message_user(
                request,
                'Недостаточно прав для отмены уведомлений.',
                level='ERROR',
            )
            return

        cancelled = 0

        for notification in queryset.filter(
            telegram_sent_at__isnull=True,
            email_sent_at__isnull=True,
        ):
            if (
                notification
                .delivery_status
                == 'cancelled'
            ):
                continue

            old_status = (
                notification
                .delivery_status
            )

            notification.delivery_status = (
                'cancelled'
            )

            notification.save(
                update_fields=[
                    'delivery_status',
                ],
            )

            self.write_admin_audit(
                request=request,
                obj=notification,
                action='admin_cancel_notification',
                old_values={
                    'delivery_status':
                        old_status,
                },
                new_values={
                    'delivery_status':
                        'cancelled',
                },
            )

            cancelled += 1

        self.message_user(
            request,
            (
                'Отменено уведомлений: '
                f'{cancelled}.'
            ),
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False
