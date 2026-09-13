from django.contrib import admin

from audit.admin_utils import (
    AdminAuditMixin,
    DangerousAdminMixin,
    NoBulkDeleteAdminMixin,
)
from exchange_rates.models import (
    Currency,
    ExchangeRate,
)


@admin.register(Currency)
class CurrencyAdmin(
    NoBulkDeleteAdminMixin,
    DangerousAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    list_display = (
        'code',
        'name',
        'kind',
        'decimal_places',
        'is_active',
    )

    list_filter = (
        'kind',
        'is_active',
    )

    search_fields = (
        'code',
        'name',
    )

    ordering = (
        'code',
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


@admin.register(ExchangeRate)
class ExchangeRateAdmin(
    NoBulkDeleteAdminMixin,
    DangerousAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    list_display = (
        'currency',
        'rate_date',
        'rate_time',
        'rate_value',
        'rate_unit',
        'source',
        'is_manual',
        'created_by',
    )

    list_filter = (
        'currency',
        'source',
        'is_manual',
        'rate_date',
    )

    search_fields = (
        'currency__code',
        'currency__name',
        'source',
        'raw_reference',
        'created_by__email',
    )

    date_hierarchy = (
        'rate_date'
    )

    ordering = (
        '-rate_date',
        'currency__code',
    )

    list_select_related = (
        'currency',
        'created_by',
    )

    autocomplete_fields = (
        'currency',
        'created_by',
    )

    readonly_fields = (
        'created_at',
    )

    fieldsets = (
        (
            'Курс',
            {
                'fields': (
                    'currency',
                    'rate_date',
                    'rate_time',
                    'rate_value',
                    'rate_unit',
                    'source',
                    'is_manual',
                ),
            },
        ),
        (
            'Источник',
            {
                'fields': (
                    'raw_reference',
                    'created_by',
                    'created_at',
                ),
            },
        ),
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
