from decimal import (
    ROUND_HALF_UP,
    Decimal,
)

from django.db import transaction
from django.utils import timezone

from audit.services import AuditService
from taxes.models import TaxPeriod


class TaxPeriodLifecycleService:
    """Подача и оплата налогового периода."""

    MONEY_QUANT = Decimal('0.01')

    def __init__(self):
        self.audit_service = AuditService()

    @transaction.atomic
    def mark_submitted(
        self,
        *,
        period,
        actor,
        submitted_at=None,
        comment='',
        confirmation_file=None,
    ):
        period = self._locked(period)

        old_values = self._audit_values(period)

        period.declaration_status = 'submitted'

        period.submitted_at = submitted_at or timezone.now()

        period.submission_comment = comment

        if confirmation_file is not None:
            if period.submission_confirmation:
                (period.submission_confirmation.delete(save=False))

            period.submission_confirmation = confirmation_file

        period.changed_after_submission = False

        period.save()

        self._audit(
            period=period,
            actor=actor,
            action='mark_submitted',
            old_values=old_values,
        )

        return period

    @transaction.atomic
    def unmark_submitted(
        self,
        *,
        period,
        actor,
    ):
        period = self._locked(period)

        old_values = self._audit_values(period)

        if period.submission_confirmation:
            (period.submission_confirmation.delete(save=False))

        period.declaration_status = 'not_submitted'

        period.submitted_at = None
        period.submission_comment = ''
        period.submission_confirmation = None

        period.changed_after_submission = False

        period.save()

        self._audit(
            period=period,
            actor=actor,
            action='unmark_submitted',
            old_values=old_values,
        )

        return period

    @transaction.atomic
    def mark_paid(
        self,
        *,
        period,
        actor,
        paid_amount,
        paid_at=None,
        comment='',
        confirmation_file=None,
    ):
        period = self._locked(period)

        paid_amount = Decimal(paid_amount).quantize(
            self.MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )

        if paid_amount < 0:
            raise ValueError('Сумма оплаты не может быть отрицательной.')

        old_values = self._audit_values(period)

        period.payment_status = 'paid'

        period.paid_at = paid_at or timezone.now()

        period.paid_amount = paid_amount

        period.payment_comment = comment

        if confirmation_file is not None:
            if period.payment_confirmation:
                (period.payment_confirmation.delete(save=False))

            period.payment_confirmation = confirmation_file

        period.save()

        self._audit(
            period=period,
            actor=actor,
            action='mark_paid',
            old_values=old_values,
        )

        return period

    @transaction.atomic
    def unmark_paid(
        self,
        *,
        period,
        actor,
    ):
        period = self._locked(period)

        old_values = self._audit_values(period)

        if period.payment_confirmation:
            (period.payment_confirmation.delete(save=False))

        period.payment_status = 'not_paid'

        period.paid_at = None

        period.paid_amount = Decimal('0.00')

        period.payment_comment = ''
        period.payment_confirmation = None

        period.save()

        self._audit(
            period=period,
            actor=actor,
            action='unmark_paid',
            old_values=old_values,
        )

        return period

    @staticmethod
    def _locked(period):
        return TaxPeriod.objects.select_for_update().get(pk=period.pk)

    def _audit(
        self,
        *,
        period,
        actor,
        action,
        old_values,
    ):
        self.audit_service.log(
            user=period.user,
            actor=actor,
            action=action,
            obj=period,
            old_values=old_values,
            new_values=(self._audit_values(period)),
        )

    @staticmethod
    def _audit_values(period):
        return {
            'declaration_status': (period.declaration_status),
            'submitted_at': (period.submitted_at),
            'payment_status': (period.payment_status),
            'paid_at': period.paid_at,
            'paid_amount': (period.paid_amount),
            'changed_after_submission': (period.changed_after_submission),
        }
