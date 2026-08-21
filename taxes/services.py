from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from incomes.models import IncomeEntry
from taxes.models import TaxPeriod


class TaxPeriodCalculationService:
    """Сервис расчёта налоговых периодов."""

    MONEY_QUANT = Decimal('0.01')

    @transaction.atomic
    def recalculate_period(
        self,
        *,
        user,
        year,
        month,
        deadline=None,
    ):
        if month < 1 or month > 12:
            raise ValidationError('Месяц должен быть от 1 до 12.')

        period = TaxPeriod.objects.filter(
            user=user,
            year=year,
            month=month,
        ).first()

        if period is None and deadline is None:
            raise ValidationError('Для нового налогового периода необходимо указать deadline.')

        incomes = IncomeEntry.objects.filter(
            user=user,
            received_at__year=year,
            received_at__month=month,
            is_deleted=False,
        )

        sums = incomes.aggregate(
            field_18=Sum(
                'amount_gel',
                filter=Q(declaration_category='cash_register_18'),
                default=Decimal('0.00'),
            ),
            field_19=Sum(
                'amount_gel',
                filter=Q(declaration_category='physical_pos_19'),
                default=Decimal('0.00'),
            ),
            field_20=Sum(
                'amount_gel',
                filter=Q(declaration_category='cashless_20'),
                default=Decimal('0.00'),
            ),
            field_21=Sum(
                'amount_gel',
                filter=Q(declaration_category='other_21'),
                default=Decimal('0.00'),
            ),
        )

        field_18 = self._money(sums['field_18'])
        field_19 = self._money(sums['field_19'])
        field_20 = self._money(sums['field_20'])
        field_21 = self._money(sums['field_21'])

        field_17 = self._money(field_18 + field_19 + field_20 + field_21)

        cumulative = IncomeEntry.objects.filter(
            user=user,
            received_at__year=year,
            received_at__month__lte=month,
            is_deleted=False,
        ).aggregate(
            total=Sum(
                'amount_gel',
                default=Decimal('0.00'),
            )
        )

        field_15 = self._money(cumulative['total'])

        if period is not None:
            tax_rate = period.tax_rate
        else:
            tax_rate = user.entrepreneur_profile.tax_rate

        field_26 = self._money(field_17 * tax_rate / Decimal('100'))

        old_values = None

        if period is not None:
            old_values = {
                'field_18': period.field_18,
                'field_19': period.field_19,
                'field_20': period.field_20,
                'field_21': period.field_21,
                'field_17': period.field_17,
                'field_15': period.field_15,
                'field_26': period.field_26,
            }

        if period is None:
            period = TaxPeriod(
                user=user,
                year=year,
                month=month,
                deadline=deadline,
                tax_rate=tax_rate,
            )

        period.field_18 = field_18
        period.field_19 = field_19
        period.field_20 = field_20
        period.field_21 = field_21
        period.field_17 = field_17
        period.field_15 = field_15
        period.field_26 = field_26

        period.calculation_status = 'calculated'
        period.calculated_at = timezone.now()

        if old_values is not None:
            changed = any(
                [
                    old_values['field_18'] != field_18,
                    old_values['field_19'] != field_19,
                    old_values['field_20'] != field_20,
                    old_values['field_21'] != field_21,
                    old_values['field_17'] != field_17,
                    old_values['field_15'] != field_15,
                    old_values['field_26'] != field_26,
                ]
            )

            if changed and period.declaration_status == 'submitted':
                period.changed_after_submission = True

        period.full_clean()
        period.save()

        return period

    @transaction.atomic
    def recalculate_from_month(
        self,
        *,
        user,
        year,
        month,
        deadline=None,
    ):
        current_period = self.recalculate_period(
            user=user,
            year=year,
            month=month,
            deadline=deadline,
        )

        next_periods = TaxPeriod.objects.filter(
            user=user,
            year=year,
            month__gt=month,
        ).order_by('month')

        for period in next_periods:
            self.recalculate_period(
                user=user,
                year=year,
                month=period.month,
            )

        return current_period

    @classmethod
    def _money(cls, value):
        if value is None:
            value = Decimal('0.00')

        return Decimal(value).quantize(
            cls.MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )
