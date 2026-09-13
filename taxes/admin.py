from django.contrib import admin

from audit.admin_utils import (
    AdminAuditMixin,
    DangerousAdminMixin,
    NoBulkDeleteAdminMixin,
)
from notifications.models import Notification
from taxes.models import TaxPeriod
from taxes.services import (
    TaxPeriodCalculationService,
)


@admin.register(TaxPeriod)
class TaxPeriodAdmin(
    NoBulkDeleteAdminMixin,
    DangerousAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    list_display = (
        'period_display',
        'user',
        'field_17_display',
        'field_15_display',
        'field_26_display',
        'declaration_status',
        'payment_status',
        'deadline',
        'is_overdue',
        'changed_after_submission',
    )

    list_filter = (
        'year',
        'month',
        'declaration_status',
        'payment_status',
        'is_overdue',
        'changed_after_submission',
        'calculation_status',
    )

    search_fields = (
        'user__email',
        'submission_comment',
        'payment_comment',
    )

    ordering = (
        '-year',
        '-month',
        'user__email',
    )

    list_select_related = (
        'user',
    )

    autocomplete_fields = (
        'user',
    )

    readonly_fields = (
        'field_18',
        'field_19',
        'field_20',
        'field_21',
        'field_17',
        'field_15',
        'field_26',
        'calculated_at',
        'declaration_status',
        'submitted_at',
        'submission_comment',
        'submission_confirmation',
        'payment_status',
        'paid_at',
        'paid_amount',
        'payment_comment',
        'payment_confirmation',
        'is_overdue',
        'changed_after_submission',
        'created_at',
        'updated_at',
    )

    actions = (
        'recalculate_periods',
        'create_admin_notification',
    )

    fieldsets = (
        (
            'Период',
            {
                'fields': (
                    'user',
                    'year',
                    'month',
                    'deadline',
                    'tax_rate',
                    'calculation_status',
                    'calculated_at',
                ),
            },
        ),
        (
            'Декларация',
            {
                'fields': (
                    'field_18',
                    'field_19',
                    'field_20',
                    'field_21',
                    'field_17',
                    'field_15',
                    'field_26',
                    'declaration_status',
                    'submitted_at',
                    'submission_comment',
                    'submission_confirmation',
                    'changed_after_submission',
                ),
            },
        ),
        (
            'Оплата',
            {
                'fields': (
                    'payment_status',
                    'paid_at',
                    'paid_amount',
                    'payment_comment',
                    'payment_confirmation',
                ),
            },
        ),
        (
            'Просрочка',
            {
                'fields': (
                    'is_overdue',
                ),
            },
        ),
        (
            'Служебные данные',
            {
                'fields': (
                    'created_at',
                    'updated_at',
                ),
            },
        ),
    )

    @admin.display(
        description='Период',
        ordering='year',
    )
    def period_display(
        self,
        obj,
    ):
        return (
            f'{obj.year}-'
            f'{obj.month:02d}'
        )

    @admin.display(
        description='Поле 17',
        ordering='field_17',
    )
    def field_17_display(
        self,
        obj,
    ):
        return (
            f'{obj.field_17} GEL'
        )

    @admin.display(
        description='Поле 15',
        ordering='field_15',
    )
    def field_15_display(
        self,
        obj,
    ):
        return (
            f'{obj.field_15} GEL'
        )

    @admin.display(
        description='Поле 26',
        ordering='field_26',
    )
    def field_26_display(
        self,
        obj,
    ):
        return (
            f'{obj.field_26} GEL'
        )

    @admin.action(
        description='Пересчитать выбранные периоды',
    )
    def recalculate_periods(
        self,
        request,
        queryset,
    ):
        if not self.has_dangerous_permission(
            request,
        ):
            self.message_user(
                request,
                'Недостаточно прав для пересчёта периодов.',
                level='ERROR',
            )
            return

        service = (
            TaxPeriodCalculationService()
        )

        recalculated = 0

        for period in queryset:
            old_values = {
                'field_17':
                    period.field_17,
                'field_15':
                    period.field_15,
                'field_26':
                    period.field_26,
                'is_overdue':
                    period.is_overdue,
            }

            updated = (
                service
                .recalculate_from_month(
                    user=period.user,
                    year=period.year,
                    month=period.month,
                )
            )

            self.write_admin_audit(
                request=request,
                obj=updated,
                action='admin_recalculate_tax_period',
                old_values=old_values,
                new_values={
                    'field_17':
                        updated.field_17,
                    'field_15':
                        updated.field_15,
                    'field_26':
                        updated.field_26,
                    'is_overdue':
                        updated.is_overdue,
                },
            )

            recalculated += 1

        self.message_user(
            request,
            (
                'Пересчитано периодов: '
                f'{recalculated}.'
            ),
        )

    @admin.action(
        description='Создать административное уведомление',
    )
    def create_admin_notification(
        self,
        request,
        queryset,
    ):
        created = 0

        for period in queryset:
            key = (
                'admin-tax-reminder:'
                f'{period.user_id}:'
                f'{period.year}:'
                f'{period.month}'
            )

            _, was_created = (
                Notification.objects
                .get_or_create(
                    user=period.user,
                    deduplication_key=key,
                    defaults={
                        'type':
                            'admin_tax_reminder',
                        'title':
                            'Проверьте налоговый период',
                        'message': (
                            'Администратор просит '
                            'проверить налоговый '
                            f'период '
                            f'{period.month:02d}.'
                            f'{period.year}.'
                        ),
                        'related_object_type':
                            'TaxPeriod',
                        'related_object_id':
                            period.pk,
                        'action_url':
                            f'/taxes/{period.pk}',
                        'delivery_status':
                            'pending',
                    },
                )
            )

            if was_created:
                created += 1

        self.message_user(
            request,
            (
                'Создано уведомлений: '
                f'{created}.'
            ),
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False
