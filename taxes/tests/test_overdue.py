from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import EntrepreneurProfile
from taxes.services import TaxPeriodCalculationService

User = get_user_model()


class TaxPeriodOverdueTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='overdue@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Overdue Test',
            tin='123456789',
            tax_rate=Decimal('1.00'),
        )

        self.service = TaxPeriodCalculationService()

    @patch(
        'taxes.services.timezone.localdate',
        return_value=date(2026, 9, 11),
    )
    def test_past_deadline_is_overdue(
        self,
        mocked_localdate,
    ):
        period = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=7,
        )

        self.assertEqual(
            period.deadline,
            date(2026, 8, 15),
        )

        self.assertTrue(
            period.is_overdue,
        )

    @patch(
        'taxes.services.timezone.localdate',
        return_value=date(2026, 9, 11),
    )
    def test_future_deadline_is_not_overdue(
        self,
        mocked_localdate,
    ):
        period = self.service.recalculate_period(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            period.deadline,
            date(2026, 9, 15),
        )

        self.assertFalse(
            period.is_overdue,
        )
