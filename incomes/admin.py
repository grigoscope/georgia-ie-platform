from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone
from zoneinfo import ZoneInfo

from audit.admin_utils import (
    AdminAuditMixin,
    DangerousAdminMixin,
    NoBulkDeleteAdminMixin,
)
from incomes.models import IncomeEntry


TBILISI_TZ = ZoneInfo('Asia/Tbilisi')


class IncomeMonthFilter(
    admin.SimpleListFilter,
):
    title = 'Месяц дохода'
    parameter_name = 'income_month'

    def lookups(
        self,
        request,
        model_admin,
    ):
        months = (
            IncomeEntry.objects
            .dates(
                'received_at',
                'month',
                order='DESC',
            )
        )

        return [
            (
                month.strftime(
                    '%Y-%m',
                ),
                month.strftime(
                    '%m.%Y',
                ),
            )
            for month in months
        ]

    def queryset(
        self,
        request,
        queryset,
    ):
        value = self.value()

        if not value:
            return queryset

        year, month = (
            value.split('-')
        )

        return queryset.filter(
            received_at__year=int(year),
            received_at__month=int(month),
        )


class IncomeEntryAdminForm(
    forms.ModelForm,
):
    change_reason = (
        forms.CharField(
            label='Причина изменения финансовых данных',
            required=False,
            widget=forms.Textarea(
                attrs={
                    'rows': 3,
                },
            ),
            help_text=(
                'Обязательно при изменении '
                'GEL-эквивалента или графы '
                'декларации.'
            ),
        )
    )

    class Meta:
        model = IncomeEntry
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()

        if not self.instance.pk:
            return cleaned_data

        original = (
            IncomeEntry.objects
            .get(pk=self.instance.pk)
        )

        amount_changed = (
            cleaned_data.get(
                'amount_gel',
            )
            != original.amount_gel
        )

        category_changed = (
            cleaned_data.get(
                'declaration_category',
            )
            != original
            .declaration_category
        )

        if (
            amount_changed
            or category_changed
        ):
            reason = (
                cleaned_data.get(
                    'change_reason',
                    '',
                )
                .strip()
            )

            if not reason:
                raise ValidationError(
                    {
                        'change_reason': (
                            'Укажите причину '
                            'изменения финансовых '
                            'данных.'
                        ),
                    }
                )

        return cleaned_data


@admin.register(IncomeEntry)
class IncomeEntryAdmin(
    NoBulkDeleteAdminMixin,
    DangerousAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    form = IncomeEntryAdminForm

    list_display = (
        'id',
        'user',
        'received_at',
        'original_amount_display',
        'amount_gel_display',
        'declaration_category',
        'period_display',
        'is_deleted',
    )

    list_filter = (
        'user',
        IncomeMonthFilter,
        'original_currency',
        'declaration_category',
        'payment_method',
        'is_deleted',
    )

    search_fields = (
        'user__email',
        'description',
        'document_number',
        'crypto_tx_hash',
        'counterparty__name',
        'invoice__number',
    )

    date_hierarchy = (
        'received_at'
    )

    ordering = (
        '-received_at',
        '-id',
    )

    list_select_related = (
        'user',
        'original_currency',
        'financial_account',
        'counterparty',
        'invoice',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'deleted_at',
    )

    fieldsets = (
        (
            'Доход',
            {
                'fields': (
                    'user',
                    'received_at',
                    'description',
                    'additional_info',
                    'counterparty',
                    'financial_account',
                    'payment_method',
                    'invoice',
                ),
            },
        ),
        (
            'Исходная сумма',
            {
                'fields': (
                    'original_amount',
                    'original_currency',
                    'exchange_rate_value',
                    'exchange_rate_unit',
                    'exchange_rate_source',
                    'exchange_rate_date',
                    'exchange_rate_time',
                ),
            },
        ),
        (
            'Учёт в GEL',
            {
                'fields': (
                    'amount_gel',
                    'declaration_category',
                    'vat_amount',
                    'change_reason',
                ),
            },
        ),
        (
            'Криптовалюта',
            {
                'fields': (
                    'crypto_asset',
                    'crypto_network',
                    'crypto_wallet_address',
                    'crypto_tx_hash',
                ),
            },
        ),
        (
            'Документы',
            {
                'fields': (
                    'document_number',
                    'document_date',
                    'attachment',
                    'comment',
                ),
            },
        ),
        (
            'Служебные данные',
            {
                'fields': (
                    'is_deleted',
                    'deleted_at',
                    'created_at',
                    'updated_at',
                ),
            },
        ),
    )

    autocomplete_fields = (
        'user',
        'counterparty',
        'financial_account',
        'original_currency',
    )

    @admin.display(
        description='Исходная сумма',
        ordering='original_amount',
    )
    def original_amount_display(
        self,
        obj,
    ):
        return (
            f'{obj.original_amount} '
            f'{obj.original_currency.code}'
        )

    @admin.display(
        description='GEL',
        ordering='amount_gel',
    )
    def amount_gel_display(
        self,
        obj,
    ):
        return (
            f'{obj.amount_gel} GEL'
        )

    @admin.display(
        description='Период',
        ordering='received_at',
    )
    def period_display(
        self,
        obj,
    ):
        received_at = obj.received_at

        if timezone.is_aware(
            received_at,
        ):
            received_at = (
                received_at.astimezone(
                    TBILISI_TZ,
                )
            )

        return received_at.strftime(
            '%Y-%m',
        )

    def get_readonly_fields(
        self,
        request,
        obj=None,
    ):
        readonly = list(
            super().get_readonly_fields(
                request,
                obj,
            )
        )

        if (
            obj is not None
            and not self
            .has_dangerous_permission(
                request,
            )
        ):
            readonly.extend(
                [
                    'amount_gel',
                    'declaration_category',
                ]
            )

        return tuple(readonly)

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        sensitive_before = None

        if change and obj.pk:
            original = (
                IncomeEntry.objects
                .get(pk=obj.pk)
            )

            sensitive_before = {
                'amount_gel':
                    original.amount_gel,
                'declaration_category':
                    original
                    .declaration_category,
            }

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        if (
            not change
            or sensitive_before
            is None
        ):
            return

        sensitive_after = {
            'amount_gel':
                obj.amount_gel,
            'declaration_category':
                obj
                .declaration_category,
        }

        changed = (
            sensitive_before
            != sensitive_after
        )

        if not changed:
            return

        reason = (
            form.cleaned_data.get(
                'change_reason',
                '',
            )
            .strip()
        )

        self.write_admin_audit(
            request=request,
            obj=obj,
            action=(
                'admin_financial_override'
            ),
            old_values=(
                sensitive_before
            ),
            new_values={
                **sensitive_after,
                'change_reason':
                    reason,
            },
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return (
            self.has_dangerous_permission(
                request,
            )
        )
