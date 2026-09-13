from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from config.business_time import business_date
from notifications.models import Notification, NotificationSettings
from taxes.models import TaxPeriod
from taxes.services import TaxPeriodCalculationService


class TaxReminderService:
    REMINDER_EVENTS = {
        1: 'first_reminder',
        4: 'repeat_4',
        7: 'repeat_7',
        10: 'repeat_10',
        13: 'repeat_13',
        15: 'deadline',
    }

    @classmethod
    def run(cls, *, for_date=None):
        today = for_date or business_date(timezone.now())
        year, month = cls.previous_period(today)

        users = (
            get_user_model()
            .objects
            .filter(
                is_active=True,
                entrepreneur_profile__isnull=False,
            )
            .select_related('entrepreneur_profile')
            .order_by('id')
        )

        result = {
            'date': today.isoformat(),
            'period_year': year,
            'period_month': month,
            'users_processed': 0,
            'periods_created': 0,
            'notifications_created': 0,
        }

        for user in users:
            period_existed = TaxPeriod.objects.filter(
                user=user,
                year=year,
                month=month,
            ).exists()

            period = TaxPeriodCalculationService().recalculate_period(
                user=user,
                year=year,
                month=month,
            )

            if not period_existed:
                result['periods_created'] += 1

            unresolved = (
                period.declaration_status != 'submitted'
                or period.payment_status != 'paid'
            )

            should_be_overdue = (
                today > period.deadline
                and unresolved
            )

            if period.is_overdue != should_be_overdue:
                period.is_overdue = should_be_overdue
                period.save(
                    update_fields=[
                        'is_overdue',
                        'updated_at',
                    ],
                )

            result['users_processed'] += 1

            event = cls.event_for_date(
                today=today,
                period=period,
            )

            if event is None:
                continue

            if not unresolved:
                continue

            if not cls.internal_enabled(user=user):
                continue

            _, created = cls.create_notification(
                period=period,
                event=event,
            )

            if created:
                result['notifications_created'] += 1

        return result

    @staticmethod
    def previous_period(today):
        first_day = today.replace(day=1)
        previous_day = first_day - timedelta(days=1)
        return previous_day.year, previous_day.month

    @classmethod
    def event_for_date(
        cls,
        *,
        today,
        period,
    ):
        event = cls.REMINDER_EVENTS.get(today.day)

        if event is not None:
            return event

        if today > period.deadline:
            return 'overdue'

        return None

    @staticmethod
    def internal_enabled(*, user):
        settings_obj = (
            NotificationSettings.objects
            .filter(user=user)
            .first()
        )

        if settings_obj is None:
            return True

        return (
            settings_obj.internal_enabled
            and settings_obj.tax_reminders_enabled
        )

    @classmethod
    @transaction.atomic
    def create_notification(
        cls,
        *,
        period,
        event,
    ):
        key = (
            f'tax:{period.user_id}:'
            f'{period.year}:{period.month}:'
            f'{event}:internal'
        )

        title, message = cls.message_for(
            period=period,
            event=event,
        )

        return Notification.objects.get_or_create(
            deduplication_key=key,
            defaults={
                'user': period.user,
                'type': 'tax_reminder',
                'title': title,
                'message': message,
                'related_object_type': 'TaxPeriod',
                'related_object_id': period.pk,
                'action_url': f'/taxes/{period.pk}',
                'delivery_status': 'pending',
            },
        )

    @staticmethod
    def message_for(
        *,
        period,
        event,
    ):
        period_label = (
            f'{period.month:02d}.'
            f'{period.year}'
        )

        pending = []

        if period.declaration_status != 'submitted':
            pending.append('подать декларацию')

        if period.payment_status != 'paid':
            pending.append('оплатить налог')

        actions = ' и '.join(pending)

        titles = {
            'first_reminder':
                'Налоговый период открыт',
            'repeat_4':
                'Напоминание по налоговому периоду',
            'repeat_7':
                'Напоминание по налоговому периоду',
            'repeat_10':
                'Приближается налоговый дедлайн',
            'repeat_13':
                'До налогового дедлайна осталось 2 дня',
            'deadline':
                'Сегодня налоговый дедлайн',
            'overdue':
                'Налоговый период просрочен',
        }

        title = titles[event]

        message = (
            f'{title} за {period_label}. '
            f'Необходимо {actions}. '
            f'Срок: {period.deadline:%d.%m.%Y}.'
        )

        return title, message
