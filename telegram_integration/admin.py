from django.contrib import admin

from telegram_integration.models import TelegramConnection


@admin.register(TelegramConnection)
class TelegramConnectionAdmin(
    admin.ModelAdmin,
):
    list_display = (
        'user',
        'username',
        'first_name',
        'last_name',
        'is_active',
        'linked_at',
        'last_seen_at',
    )

    list_filter = (
        'is_active',
        'language_code',
        'linked_at',
    )

    search_fields = (
        'user__email',
        'username',
        'first_name',
        'last_name',
    )

    ordering = (
        '-linked_at',
    )

    readonly_fields = (
        'user',
        'username',
        'first_name',
        'last_name',
        'language_code',
        'is_active',
        'linked_at',
        'last_seen_at',
    )

    exclude = (
        'telegram_user_id',
        'telegram_chat_id',
    )

    def has_add_permission(
        self,
        request,
    ):
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
