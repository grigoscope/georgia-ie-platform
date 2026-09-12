from django.contrib import admin

from audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'action',
        'object_type',
        'object_id',
        'user',
        'actor',
    )

    list_filter = (
        'action',
        'object_type',
        'created_at',
    )

    search_fields = (
        'user__email',
        'actor__email',
        'request_id',
        'object_type',
        '=object_id',
    )

    ordering = (
        '-created_at',
    )

    readonly_fields = (
        'user',
        'actor',
        'action',
        'object_type',
        'object_id',
        'old_values',
        'new_values',
        'request_id',
        'ip_address',
        'user_agent',
        'created_at',
    )

    fieldsets = (
        (
            'Действие',
            {
                'fields': (
                    'created_at',
                    'action',
                    'object_type',
                    'object_id',
                ),
            },
        ),
        (
            'Пользователи',
            {
                'fields': (
                    'user',
                    'actor',
                ),
            },
        ),
        (
            'Изменения',
            {
                'fields': (
                    'old_values',
                    'new_values',
                ),
            },
        ),
        (
            'Запрос',
            {
                'fields': (
                    'request_id',
                    'ip_address',
                    'user_agent',
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False
