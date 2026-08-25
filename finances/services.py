from django.core.exceptions import ValidationError
from django.db import transaction

from finances.models import FinancialAccount


class FinancialAccountService:
    """Бизнес-логика финансовых счетов."""

    @transaction.atomic
    def create(
        self,
        *,
        user,
        **data,
    ):
        account = FinancialAccount(
            user=user,
            **data,
        )

        account.full_clean()
        account.save()

        return account

    @transaction.atomic
    def update(
        self,
        *,
        account,
        **data,
    ):
        account = FinancialAccount.objects.select_for_update().get(pk=account.pk)

        for field, value in data.items():
            setattr(
                account,
                field,
                value,
            )

        account.full_clean()
        account.save()

        return account

    @transaction.atomic
    def set_default(
        self,
        *,
        account,
    ):
        account = FinancialAccount.objects.select_for_update().get(pk=account.pk)

        if not account.is_active:
            raise ValidationError('Архивный счёт нельзя сделать счётом по умолчанию.')

        (
            FinancialAccount.objects.filter(
                user=account.user,
                is_default=True,
            )
            .exclude(pk=account.pk)
            .update(is_default=False)
        )

        account.is_default = True

        account.save(
            update_fields=[
                'is_default',
                'updated_at',
            ]
        )

        return account

    @transaction.atomic
    def archive(
        self,
        *,
        account,
    ):
        account = FinancialAccount.objects.select_for_update().get(pk=account.pk)

        account.is_active = False
        account.is_default = False
        account.use_in_invoices = False

        account.save(
            update_fields=[
                'is_active',
                'is_default',
                'use_in_invoices',
                'updated_at',
            ]
        )

        return account
