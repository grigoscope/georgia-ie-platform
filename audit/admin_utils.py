from audit.services import AuditService


DANGEROUS_ADMIN_GROUP = 'Финансовые администраторы'


class NoBulkDeleteAdminMixin:
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions


class DangerousAdminMixin:
    def has_dangerous_permission(self, request):
        return (
            request.user.is_superuser
            or request.user.groups.filter(
                name=DANGEROUS_ADMIN_GROUP,
            ).exists()
        )


class AdminAuditMixin:
    def get_audit_owner(self, obj):
        if obj.__class__.__name__ == 'User':
            return obj

        user = getattr(obj, 'user', None)

        if user is not None:
            return user

        invoice = getattr(obj, 'invoice', None)

        if invoice is not None:
            return invoice.user

        return None

    def get_audit_snapshot(self, obj):
        values = {}

        for field in obj._meta.concrete_fields:
            value = getattr(obj, field.attname)

            if hasattr(value, 'name'):
                value = value.name

            values[field.name] = value

        return values

    def get_request_audit_data(self, request):
        forwarded_for = request.META.get(
            'HTTP_X_FORWARDED_FOR',
            '',
        )

        if forwarded_for:
            ip_address = (
                forwarded_for
                .split(',')[0]
                .strip()
            )
        else:
            ip_address = request.META.get(
                'REMOTE_ADDR',
            )

        return {
            'request_id': request.headers.get(
                'X-Request-ID',
                '',
            ),
            'ip_address': ip_address,
            'user_agent': request.META.get(
                'HTTP_USER_AGENT',
                '',
            ),
        }

    def write_admin_audit(
        self,
        *,
        request,
        obj,
        action,
        old_values=None,
        new_values=None,
    ):
        AuditService.log(
            user=self.get_audit_owner(obj),
            actor=request.user,
            action=action,
            obj=obj,
            old_values=old_values or {},
            new_values=new_values or {},
            **self.get_request_audit_data(request),
        )

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        old_values = {}

        if change and obj.pk:
            old_obj = (
                obj.__class__
                ._default_manager
                .get(pk=obj.pk)
            )

            old_values = self.get_audit_snapshot(
                old_obj,
            )

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        new_values = self.get_audit_snapshot(obj)

        if change:
            old_changed = {}
            new_changed = {}

            for key, old_value in old_values.items():
                new_value = new_values.get(key)

                if old_value != new_value:
                    old_changed[key] = old_value
                    new_changed[key] = new_value

            if not new_changed:
                return

            self.write_admin_audit(
                request=request,
                obj=obj,
                action='admin_update',
                old_values=old_changed,
                new_values=new_changed,
            )

            return

        self.write_admin_audit(
            request=request,
            obj=obj,
            action='admin_create',
            new_values=new_values,
        )

    def delete_model(
        self,
        request,
        obj,
    ):
        old_values = self.get_audit_snapshot(obj)

        self.write_admin_audit(
            request=request,
            obj=obj,
            action='admin_delete',
            old_values=old_values,
        )

        super().delete_model(
            request,
            obj,
        )
