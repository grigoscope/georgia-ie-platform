from django.contrib import admin

from audit.admin_utils import (
    AdminAuditMixin,
    DangerousAdminMixin,
    NoBulkDeleteAdminMixin,
)
from finances.models import (
    Counterparty,
    FinancialAccount,
)


@admin.register(FinancialAccount)
class FinancialAccountAdmin(
    NoBulkDeleteAdminMixin,
    DangerousAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    list_display = (
        'id',
        'user',
        'name',
        'type',
        'default_currency',
        'provider_name',
        'is_default',
        'use_in_invoices',
        'is_active',
    )

    list_filter = (
        'type',
        'default_currency',
        'is_default',
        'use_in_invoices',
        'is_active',
    )

    search_fields = (
        'user__email',
        'name',
        'provider_name',
        'account_holder',
        'iban',
        'swift_bic',
        'crypto_asset',
        'crypto_network',
    )

    ordering = (
        'user__email',
        'name',
    )

    list_select_related = (
        'user',
        'default_currency',
    )

    autocomplete_fields = (
        'user',
        'default_currency',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (
            'Счёт',
            {
                'fields': (
                    'user',
                    'name',
                    'type',
                    'default_currency',
                    'provider_name',
                    'account_holder',
                ),
            },
        ),
        (
            'Банковские реквизиты',
            {
                'fields': (
                    'iban',
                    'swift_bic',
                    'account_identifier',
                ),
            },
        ),
        (
            'Криптокошелёк',
            {
                'fields': (
                    'crypto_asset',
                    'crypto_network',
                    'wallet_address',
                    'memo_tag',
                ),
            },
        ),
        (
            'Учёт',
            {
                'fields': (
                    'default_declaration_category',
                    'payment_instructions',
                    'is_default',
                    'use_in_invoices',
                    'is_active',
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


@admin.register(Counterparty)
class CounterpartyAdmin(
    NoBulkDeleteAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    list_display = (
        'id',
        'user',
        'name',
        'type',
        'country',
        'tax_id',
        'email',
    )

    list_filter = (
        'type',
        'country',
    )

    search_fields = (
        'user__email',
        'name',
        'tax_id',
        'email',
        'phone',
    )

    ordering = (
        'user__email',
        'name',
    )

    list_select_related = (
        'user',
    )

    autocomplete_fields = (
        'user',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )
