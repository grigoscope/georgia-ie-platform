from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import ActionForm

from audit.admin_utils import (
    AdminAuditMixin,
    DangerousAdminMixin,
    NoBulkDeleteAdminMixin,
)
from notifications.models import Notification
from taxes.lifecycle_services import TaxPeriodLifecycleService
from taxes.models import TaxPeriod
from taxes.services import TaxPeriodCalculationService


class TaxPeriodActionForm(ActionForm):
    reason = forms.CharField(
        label='Причина',
        required=False,
        max_length=500,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Причина административного действия',
                'style': 'min-width: 320px;',
            },
        ),
    )


@admin.register(TaxPeriod)
class TaxPeriodAdmin(
    NoBulkDeleteAdminMixin,
    DangerousAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    action_form = TaxPeriodActionForm

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

    list_select_related = ('user',)
    autocomplete_fields = ('user',)

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
        'unmark_submitted_with_reason',
        'unmark_paid_with_reason',
    )

    @admin.display(description='Период', ordering='year')
    def period_display(self, obj):
        return f'{obj.year}-{obj.month:02d}'

    @admin.display(description='Поле 17', ordering='field_17')
    def field_17_display(self, obj):
        return f'{obj.field_17} GEL'

    @admin.display(description='Поле 15', ordering='field_15')
    def field_15_display(self, obj):
        return f'{obj.field_15} GEL'

    @admin.display(description='Поле 26', ordering='field_26')
    def field_26_display(self, obj):
        return f'{obj.field_26} GEL'

    def _require_reason(self, request):
        reason = request.POST.get('reason', '').strip()

        if reason:
            return reason

        self.message_user(
            request,
            'Для этого действия обязательно укажите причину.',
            level='ERROR',
        )
        return None

    @admin.action(description='Пересчитать выбранные периоды')
    def recalculate_periods(self, request, queryset):
        if not self.has_dangerous_permission(request):
            self.message_user(
                request,
                'Недостаточно прав для пересчёта периодов.',
                level='ERROR',
            )
            return

        service = TaxPeriodCalculationService()
        recalculated = 0

        for period in queryset:
            old_values = {
                'field_17': period.field_17,
                'field_15': period.field_15,
                'field_26': period.field_26,
                'is_overdue': period.is_overdue,
            }

            updated = service.recalculate_from_month(
                user=period.user,
                year=period.year,
                month=period.month,
            )

            self.write_admin_audit(
                request=request,
                obj=updated,
                action='admin_recalculate_tax_period',
                old_values=old_values,
                new_values={
                    'field_17': updated.field_17,
                    'field_15': updated.field_15,
                    'field_26': updated.field_26,
                    'is_overdue': updated.is_overdue,
                },
            )
            recalculated += 1

        self.message_user(
            request,
            f'Пересчитано периодов: {recalculated}.',
        )

    @admin.action(description='Создать административное уведомление')
    def create_admin_notification(self, request, queryset):
        created = 0

        for period in queryset:
            key = (
                f'admin-tax-reminder:{period.user_id}:'
                f'{period.year}:{period.month}'
            )

            _, was_created = Notification.objects.get_or_create(
                user=period.user,
                deduplication_key=key,
                defaults={
                    'type': 'admin_tax_reminder',
                    'title': 'Проверьте налоговый период',
                    'message': (
                        'Администратор просит проверить налоговый '
                        f'период {period.month:02d}.{period.year}.'
                    ),
                    'related_object_type': 'TaxPeriod',
                    'related_object_id': period.pk,
                    'action_url': f'/taxes/{period.pk}',
                    'delivery_status': 'pending',
                },
            )

            if was_created:
                created += 1

        self.message_user(request, f'Создано уведомлений: {created}.')

    @admin.action(description='Снять отметку подачи с причиной')
    def unmark_submitted_with_reason(self, request, queryset):
        if not self.has_dangerous_permission(request):
            self.message_user(
                request,
                'Недостаточно прав для снятия отметки подачи.',
                level='ERROR',
            )
            return

        reason = self._require_reason(request)
        if reason is None:
            return

        service = TaxPeriodLifecycleService()
        changed = 0

        for period in queryset:
            if period.declaration_status != 'submitted':
                continue

            old_values = {
                'declaration_status': period.declaration_status,
                'submitted_at': period.submitted_at,
                'submission_comment': period.submission_comment,
            }

            updated = service.unmark_submitted(
                period=period,
                actor=request.user,
            )

            self.write_admin_audit(
                request=request,
                obj=updated,
                action='admin_unmark_submitted_with_reason',
                old_values=old_values,
                new_values={
                    'declaration_status': updated.declaration_status,
                    'reason': reason,
                },
            )
            changed += 1

        self.message_user(request, f'Снята отметка подачи: {changed}.')

    @admin.action(description='Снять отметку оплаты с причиной')
    def unmark_paid_with_reason(self, request, queryset):
        if not self.has_dangerous_permission(request):
            self.message_user(
                request,
                'Недостаточно прав для снятия отметки оплаты.',
                level='ERROR',
            )
            return

        reason = self._require_reason(request)
        if reason is None:
            return

        service = TaxPeriodLifecycleService()
        changed = 0

        for period in queryset:
            if period.payment_status != 'paid':
                continue

            old_values = {
                'payment_status': period.payment_status,
                'paid_at': period.paid_at,
                'paid_amount': period.paid_amount,
                'payment_comment': period.payment_comment,
            }

            updated = service.unmark_paid(
                period=period,
                actor=request.user,
            )

            self.write_admin_audit(
                request=request,
                obj=updated,
                action='admin_unmark_paid_with_reason',
                old_values=old_values,
                new_values={
                    'payment_status': updated.payment_status,
                    'reason': reason,
                },
            )
            changed += 1

        self.message_user(request, f'Снята отметка оплаты: {changed}.')

    def has_delete_permission(self, request, obj=None):
        return False
