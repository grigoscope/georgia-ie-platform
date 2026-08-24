from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone


def get_business_timezone():
    """Бизнес-таймзона приложения."""

    return ZoneInfo(
        getattr(
            settings,
            'BUSINESS_TIME_ZONE',
            'Asia/Tbilisi',
        )
    )


def to_business_datetime(value):
    """Перевести datetime в бизнес-таймзону."""

    tz = get_business_timezone()

    if timezone.is_naive(value):
        return timezone.make_aware(
            value,
            timezone=tz,
        )

    return value.astimezone(tz)


def business_date(value):
    """Получить локальную бизнес-дату."""

    return to_business_datetime(value).date()


def business_period(value):
    """Получить business year/month."""

    local_value = to_business_datetime(value)

    return (
        local_value.year,
        local_value.month,
    )


def period_bounds(
    *,
    year,
    month,
):
    """
    Начало и конец месяца
    в Asia/Tbilisi.

    Используется как:
    received_at__gte=start
    received_at__lt=end
    """

    if month < 1 or month > 12:
        raise ValueError('Месяц должен быть от 1 до 12.')

    tz = get_business_timezone()

    start = datetime(
        year,
        month,
        1,
        tzinfo=tz,
    )

    if month == 12:
        end = datetime(
            year + 1,
            1,
            1,
            tzinfo=tz,
        )
    else:
        end = datetime(
            year,
            month + 1,
            1,
            tzinfo=tz,
        )

    return start, end


def year_bounds(*, year):
    """Границы календарного года."""

    tz = get_business_timezone()

    return (
        datetime(
            year,
            1,
            1,
            tzinfo=tz,
        ),
        datetime(
            year + 1,
            1,
            1,
            tzinfo=tz,
        ),
    )
