from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ObjectDoesNotExist

from accounts.models import EntrepreneurProfile, User
from audit.admin_utils import (
    AdminAuditMixin,
    DangerousAdminMixin,
    NoBulkDeleteAdminMixin,
)
from audit.services import AuditService


@admin.register(User)
class CustomUserAdmin(
    NoBulkDeleteAdminMixin,
    DangerousAdminMixin,
    AdminAuditMixin,
    UserAdmin,
):
    list_display = (
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'telegram_status',
        'profile_status',
        'date_joined',
    )

    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    )

    search_fields = (
        'email',
        'first_name',
        'last_name',
        'telegram_connection__username',
        'entrepreneur_profile__business_name',
        'entrepreneur_profile__tin',
    )

    ordering = (
        'email',
    )

    readonly_fields = (
        'last_login',
        'date_joined',
        'token_version',
    )

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'email',
                    'password',
                ),
            },
        ),
        (
            'Личные данные',
            {
                'fields': (
                    'first_name',
                    'last_name',
                ),
            },
        ),
        (
            'Доступ',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (
            'Служебные данные',
            {
                'fields': (
                    'last_login',
                    'date_joined',
                    'token_version',
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': (
                    'wide',
                ),
                'fields': (
                    'email',
                    'password1',
                    'password2',
                    'is_active',
                    'is_staff',
                ),
            },
        ),
    )

    actions = (
        'block_users',
        'unblock_users',
        'reset_telegram_links',
    )

    @admin.display(
        description='Telegram',
        boolean=True,
    )
    def telegram_status(self, obj):
        try:
            return (
                obj.telegram_connection
                .is_active
            )
        except ObjectDoesNotExist:
            return False

    @admin.display(
        description='Профиль заполнен',
        boolean=True,
    )
    def profile_status(self, obj):
        try:
            profile = obj.entrepreneur_profile
        except ObjectDoesNotExist:
            return False

        return bool(
            profile.business_name
            and profile.tin
        )

    @admin.action(
        description='Заблокировать пользователей',
    )
    def block_users(
        self,
        request,
        queryset,
    ):
        if not self.has_dangerous_permission(
            request,
        ):
            self.message_user(
                request,
                'Недостаточно прав для блокировки пользователей.',
                level='ERROR',
            )
            return

        changed = 0

        for user in queryset:
            if (
                user.is_superuser
                or not user.is_active
            ):
                continue

            user.is_active = False
            user.save(
                update_fields=[
                    'is_active',
                ],
            )

            AuditService.log(
                user=user,
                actor=request.user,
                action='admin_block_user',
                obj=user,
                old_values={
                    'is_active': True,
                },
                new_values={
                    'is_active': False,
                },
                **self.get_request_audit_data(
                    request,
                ),
            )

            changed += 1

        self.message_user(
            request,
            (
                'Заблокировано пользователей: '
                f'{changed}.'
            ),
        )

    @admin.action(
        description='Разблокировать пользователей',
    )
    def unblock_users(
        self,
        request,
        queryset,
    ):
        if not self.has_dangerous_permission(
            request,
        ):
            self.message_user(
                request,
                'Недостаточно прав для разблокировки пользователей.',
                level='ERROR',
            )
            return

        changed = 0

        for user in queryset:
            if user.is_active:
                continue

            user.is_active = True
            user.save(
                update_fields=[
                    'is_active',
                ],
            )

            AuditService.log(
                user=user,
                actor=request.user,
                action='admin_unblock_user',
                obj=user,
                old_values={
                    'is_active': False,
                },
                new_values={
                    'is_active': True,
                },
                **self.get_request_audit_data(
                    request,
                ),
            )

            changed += 1

        self.message_user(
            request,
            (
                'Разблокировано пользователей: '
                f'{changed}.'
            ),
        )

    @admin.action(
        description='Сбросить Telegram-связь',
    )
    def reset_telegram_links(
        self,
        request,
        queryset,
    ):
        if not self.has_dangerous_permission(
            request,
        ):
            self.message_user(
                request,
                'Недостаточно прав для сброса Telegram-связи.',
                level='ERROR',
            )
            return

        changed = 0

        for user in queryset:
            try:
                connection = user.telegram_connection
            except ObjectDoesNotExist:
                continue

            old_values = {
                'telegram_user_id':
                    connection.telegram_user_id,
                'username':
                    connection.username,
                'is_active':
                    connection.is_active,
            }

            connection.delete()

            AuditService.log(
                user=user,
                actor=request.user,
                action='admin_reset_telegram',
                obj=user,
                old_values=old_values,
                new_values={
                    'telegram_connection':
                        None,
                },
                **self.get_request_audit_data(
                    request,
                ),
            )

            changed += 1

        self.message_user(
            request,
            (
                'Сброшено Telegram-связей: '
                f'{changed}.'
            ),
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return self.has_dangerous_permission(
            request,
        )


@admin.register(EntrepreneurProfile)
class EntrepreneurProfileAdmin(
    NoBulkDeleteAdminMixin,
    AdminAuditMixin,
    admin.ModelAdmin,
):
    list_display = (
        'user',
        'business_name',
        'tin',
        'entrepreneur_status',
        'tax_rate',
        'timezone',
        'updated_at',
    )

    list_filter = (
        'entrepreneur_status',
        'language',
        'timezone',
    )

    search_fields = (
        'user__email',
        'business_name',
        'tin',
        'phone',
        'public_email',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    autocomplete_fields = (
        'user',
    )

    fieldsets = (
        (
            'ИП',
            {
                'fields': (
                    'user',
                    'business_name',
                    'entrepreneur_status',
                    'tin',
                    'legal_address',
                    'phone',
                    'public_email',
                ),
            },
        ),
        (
            'Налоги и учёт',
            {
                'fields': (
                    'tax_rate',
                    'accounting_start_date',
                    'timezone',
                    'language',
                ),
            },
        ),
        (
            'Инвойсы',
            {
                'fields': (
                    'invoice_prefix',
                    'next_invoice_number',
                    'signature_file',
                    'logo_file',
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


admin.site.site_header = (
    'Georgia IE — администрирование'
)

admin.site.site_title = (
    'Georgia IE Admin'
)

admin.site.index_title = (
    'Управление платформой'
)
