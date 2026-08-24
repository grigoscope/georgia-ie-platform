from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import FinancialAccount
from incomes.models import IncomeEntry
from notifications.models import Notification
from taxes.services import TaxPeriodCalculationService

User = get_user_model()


class TaxPeriodNotificationTests(TestCase):
    """Уведомления об изменении поданной декларации."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Entrepreneur',
            tin='123456789',
            tax_rate=Decimal('1.00'),
        )

        self.gel = Currency.objects.create(
            code='GEL',
            name='Georgian Lari',
            kind='fiat',
            decimal_places=2,
        )

        self.account = FinancialAccount.objects.create(
            user=self.user,
            name='TBC GEL',
            type='bank_account',
            default_currency=self.gel,
            default_declaration_category='cashless_20',
        )

        self.service = TaxPeriodCalculationService()

        self.deadline = date(
            2026,
            9,
            15,
        )

    def _received_at(self, day):
        return timezone.make_aware(
            datetime(
                2026,
                8,
                day,
                12,
                0,
            )
        )

    def _create_income(
        self,
        *,
        amount,
        day,
    ):
        return IncomeEntry.objects.create(
            user=self.user,
            received_at=self._received_at(day),
            description='Test income',
            financial_account=self.account,
            original_amount=Decimal(str(amount)),
            original_currency=self.gel,
            exchange_rate_value=Decimal('1'),
            exchange_rate_unit=1,
            exchange_rate_source='GEL',
            exchange_rate_date=date(
                2026,
                8,
                day,
            ),
            amount_gel=Decimal(str(amount)),
            declaration_category='cashless_20',
        )

    def _create_initial_period(self):
        self._create_income(
            amount='100.00',
            day=5,
        )

        return self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
            deadline=self.deadline,
        )

    def test_submitted_period_change_creates_notification(
        self,
    ):
        period = self._create_initial_period()

        period.declaration_status = 'submitted'
        period.submitted_at = timezone.now()

        period.save(
            update_fields=[
                'declaration_status',
                'submitted_at',
                'updated_at',
            ]
        )

        self._create_income(
            amount='50.00',
            day=10,
        )

        self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        period.refresh_from_db()

        self.assertTrue(period.changed_after_submission)

        self.assertEqual(
            period.declaration_status,
            'submitted',
        )

        self.assertEqual(
            period.field_20,
            Decimal('150.00'),
        )

        self.assertEqual(
            Notification.objects.count(),
            1,
        )

        notification = Notification.objects.get()

        self.assertEqual(
            notification.user,
            self.user,
        )

        self.assertEqual(
            notification.type,
            'tax_period_changed',
        )

        self.assertEqual(
            notification.related_object_type,
            'TaxPeriod',
        )

        self.assertEqual(
            notification.related_object_id,
            period.id,
        )

        self.assertEqual(
            notification.deduplication_key,
            (f'tax-period-changed:{self.user.id}:2026:8'),
        )

    def test_recalculation_does_not_duplicate_notification(
        self,
    ):
        period = self._create_initial_period()

        period.declaration_status = 'submitted'
        period.submitted_at = timezone.now()

        period.save(
            update_fields=[
                'declaration_status',
                'submitted_at',
                'updated_at',
            ]
        )

        self._create_income(
            amount='50.00',
            day=10,
        )

        self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            Notification.objects.count(),
            1,
        )

        self._create_income(
            amount='25.00',
            day=15,
        )

        self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        period.refresh_from_db()

        self.assertEqual(
            period.field_20,
            Decimal('175.00'),
        )

        self.assertTrue(period.changed_after_submission)

        self.assertEqual(
            Notification.objects.count(),
            1,
        )

    def test_not_submitted_period_does_not_create_notification(
        self,
    ):
        period = self._create_initial_period()

        self.assertEqual(
            period.declaration_status,
            'not_submitted',
        )

        self._create_income(
            amount='50.00',
            day=10,
        )

        self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        period.refresh_from_db()

        self.assertEqual(
            period.field_20,
            Decimal('150.00'),
        )

        self.assertFalse(period.changed_after_submission)

        self.assertEqual(
            Notification.objects.count(),
            0,
        )

    def test_recalculation_without_changes_does_not_notify(
        self,
    ):
        period = self._create_initial_period()

        period.declaration_status = 'submitted'
        period.submitted_at = timezone.now()

        period.save(
            update_fields=[
                'declaration_status',
                'submitted_at',
                'updated_at',
            ]
        )

        self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        period.refresh_from_db()

        self.assertFalse(period.changed_after_submission)

        self.assertEqual(
            Notification.objects.count(),
            0,
        )

    def test_new_period_does_not_create_notification(
        self,
    ):
        self._create_income(
            amount='100.00',
            day=5,
        )

        period = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
            deadline=self.deadline,
        )

        self.assertEqual(
            period.field_20,
            Decimal('100.00'),
        )

        self.assertFalse(period.changed_after_submission)

        self.assertEqual(
            Notification.objects.count(),
            0,
        )
