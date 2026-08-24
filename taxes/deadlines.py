from datetime import date

from django.core.exceptions import ValidationError


class TaxDeadlineService:
    """Расчёт сроков налоговой декларации."""

    DEADLINE_DAY = 15

    @classmethod
    def calculate(
        cls,
        *,
        year,
        month,
    ):
        """
        Для малого бизнеса:
        15-е число месяца,
        следующего за отчётным.
        """

        if month < 1 or month > 12:
            raise ValidationError('Месяц должен быть от 1 до 12.')

        if month == 12:
            deadline_year = year + 1
            deadline_month = 1

        else:
            deadline_year = year
            deadline_month = month + 1

        return date(
            deadline_year,
            deadline_month,
            cls.DEADLINE_DAY,
        )
