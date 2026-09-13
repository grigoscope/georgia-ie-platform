from datetime import date
from decimal import Decimal

from django.test import TestCase

from accounts.models import (
    EntrepreneurProfile,
    User,
)
from notifications.models import (
    Notification,
    NotificationSettings,
)
from notifications.tax_reminders import (
    TaxReminderService,
)
from taxes.models import TaxPeriod


class TaxReminderServiceTests(
    TestCase,
):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                email='tax-cycle@example.com',
                password='Password123!',
            )
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Tax Cycle IE',
            tin='123456789',
            tax_rate=Decimal('1.00'),
        )

    def test_creates_zero_period_automatically(
        self,
    ):
        result = TaxReminderService.run(
            for_date=date(
                2026,
                10,
                1,
            ),
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=9,
        )

        self.assertEqual(
            period.field_17,
            Decimal('0.00'),
        )

        self.assertEqual(
            result['periods_created'],
            1,
        )

    def test_creates_all_scheduled_events(
        self,
    ):
        expected = {
            1: 'first_reminder',
            4: 'repeat_4',
            7: 'repeat_7',
            10: 'repeat_10',
            13: 'repeat_13',
            15: 'deadline',
        }

        for day, event in expected.items():
            with self.subTest(day=day):
                TaxReminderService.run(
                    for_date=date(
                        2026,
                        10,
                        day,
                    ),
                )

                key = (
                    f'tax:{self.user.id}:'
                    f'2026:9:{event}:internal'
                )

                self.assertTrue(
                    Notification.objects.filter(
                        deduplication_key=key,
                    ).exists()
                )

    def test_repeat_run_does_not_duplicate_notification(
        self,
    ):
        target_date = date(
            2026,
            10,
            4,
        )

        TaxReminderService.run(
            for_date=target_date,
        )

        TaxReminderService.run(
            for_date=target_date,
        )

        key = (
            f'tax:{self.user.id}:'
            '2026:9:repeat_4:internal'
        )

        self.assertEqual(
            Notification.objects.filter(
                deduplication_key=key,
            ).count(),
            1,
        )

    def test_overdue_event_after_deadline(
        self,
    ):
        TaxReminderService.run(
            for_date=date(
                2026,
                10,
                16,
            ),
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=9,
        )

        self.assertTrue(
            period.is_overdue,
        )

        key = (
            f'tax:{self.user.id}:'
            '2026:9:overdue:internal'
        )

        self.assertTrue(
            Notification.objects.filter(
                deduplication_key=key,
            ).exists()
        )

    def test_no_notification_when_everything_is_closed(
        self,
    ):
        TaxReminderService.run(
            for_date=date(
                2026,
                10,
                1,
            ),
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=9,
        )

        period.declaration_status = (
            'submitted'
        )

        period.payment_status = (
            'paid'
        )

        period.save(
            update_fields=[
                'declaration_status',
                'payment_status',
                'updated_at',
            ],
        )

        TaxReminderService.run(
            for_date=date(
                2026,
                10,
                4,
            ),
        )

        key = (
            f'tax:{self.user.id}:'
            '2026:9:repeat_4:internal'
        )

        self.assertFalse(
            Notification.objects.filter(
                deduplication_key=key,
            ).exists()
        )

    def test_notification_continues_if_only_one_action_is_done(
        self,
    ):
        TaxReminderService.run(
            for_date=date(
                2026,
                10,
                1,
            ),
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=9,
        )

        period.declaration_status = (
            'submitted'
        )

        period.save(
            update_fields=[
                'declaration_status',
                'updated_at',
            ],
        )

        TaxReminderService.run(
            for_date=date(
                2026,
                10,
                4,
            ),
        )

        notification = Notification.objects.get(
            deduplication_key=(
                f'tax:{self.user.id}:'
                '2026:9:repeat_4:internal'
            ),
        )

        self.assertIn(
            'оплатить налог',
            notification.message,
        )

        self.assertNotIn(
            'подать декларацию',
            notification.message,
        )

    def test_disabled_tax_reminders_stop_notifications(
        self,
    ):
        NotificationSettings.objects.create(
            user=self.user,
            internal_enabled=True,
            tax_reminders_enabled=False,
        )

        TaxReminderService.run(
            for_date=date(
                2026,
                10,
                1,
            ),
        )

        self.assertEqual(
            Notification.objects.count(),
            0,
        )
