from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import (
    get_user_model,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import (
    EntrepreneurProfile,
)
from audit.models import AuditLog
from exchange_rates.models import Currency
from finances.models import (
    FinancialAccount,
)
from incomes.models import IncomeEntry
from taxes.models import TaxPeriod

User = get_user_model()


class TaxPeriodV1APITests(APITestCase):
    """Stage 4 API налогов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            tin='123456789',
            tax_rate=Decimal('1.00'),
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='StrongPass123!',
        )

        EntrepreneurProfile.objects.create(
            user=self.other_user,
            business_name='Other',
            tin='987654321',
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
        )

        self.client.force_authenticate(user=self.user)

    def _create_income(
        self,
        amount='1000.00',
    ):
        received_at = datetime(
            2026,
            8,
            10,
            12,
            tzinfo=ZoneInfo('Asia/Tbilisi'),
        )

        return IncomeEntry.objects.create(
            user=self.user,
            received_at=received_at,
            description='Test income',
            financial_account=(self.account),
            original_amount=Decimal(amount),
            original_currency=self.gel,
            exchange_rate_value=Decimal('1'),
            exchange_rate_unit=1,
            exchange_rate_source='GEL',
            exchange_rate_date=(received_at.date()),
            amount_gel=Decimal(amount),
            declaration_category=('cashless_20'),
        )

    def _generate(self):
        return self.client.post(
            reverse('v1-tax-period-generate'),
            {
                'year': 2026,
                'month': 8,
            },
            format='json',
        )

    def test_requires_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse('v1-tax-period-list'))

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_generate_period(self):
        self._create_income('1350.00')

        response = self._generate()

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            period.field_20,
            Decimal('1350.00'),
        )

        self.assertEqual(
            period.field_17,
            Decimal('1350.00'),
        )

        self.assertEqual(
            period.field_26,
            Decimal('13.50'),
        )

    def test_generate_is_idempotent(
        self,
    ):
        self._create_income()

        first = self._generate()
        second = self._generate()

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            TaxPeriod.objects.filter(
                user=self.user,
                year=2026,
                month=8,
            ).count(),
            1,
        )

    def test_foreign_period_is_hidden(
        self,
    ):
        period = TaxPeriod.objects.create(
            user=self.other_user,
            year=2026,
            month=8,
            deadline='2026-09-15',
        )

        response = self.client.get(
            reverse(
                'v1-tax-period-detail',
                args=[period.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_preview_tax_rate(
        self,
    ):
        self._create_income('1000.00')

        response = self._generate()

        period_id = response.data['id']

        response = self.client.post(
            reverse(
                ('v1-tax-period-preview-tax-rate'),
                args=[period_id],
            ),
            {
                'tax_rate': '3.00',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['data']['field_26'],
            '30.00',
        )

        period = TaxPeriod.objects.get(id=period_id)

        self.assertEqual(
            period.tax_rate,
            Decimal('1.00'),
        )

        self.assertEqual(
            period.field_26,
            Decimal('10.00'),
        )

    def test_mark_and_unmark_submitted(
        self,
    ):
        self._create_income()

        response = self._generate()

        period_id = response.data['id']

        response = self.client.post(
            reverse(
                ('v1-tax-period-mark-submitted'),
                args=[period_id],
            ),
            {
                'comment': ('Submitted manually'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        period = TaxPeriod.objects.get(id=period_id)

        self.assertEqual(
            period.declaration_status,
            'submitted',
        )

        self.assertIsNotNone(period.submitted_at)

        self.assertTrue(
            AuditLog.objects.filter(
                object_type='TaxPeriod',
                object_id=period.id,
                action='mark_submitted',
            ).exists()
        )

        response = self.client.post(
            reverse(
                ('v1-tax-period-unmark-submitted'),
                args=[period_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        period.refresh_from_db()

        self.assertEqual(
            period.declaration_status,
            'not_submitted',
        )

        self.assertIsNone(period.submitted_at)

    def test_recalculate_submitted_period_sets_warning(
        self,
    ):
        self._create_income('1000.00')

        response = self._generate()

        period_id = response.data['id']

        self.client.post(
            reverse(
                ('v1-tax-period-mark-submitted'),
                args=[period_id],
            ),
            {},
            format='json',
        )

        self._create_income('500.00')

        response = self.client.post(
            reverse(
                ('v1-tax-period-recalculate'),
                args=[period_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        period = TaxPeriod.objects.get(id=period_id)

        self.assertEqual(
            period.field_17,
            Decimal('1500.00'),
        )

        self.assertEqual(
            period.declaration_status,
            'submitted',
        )

        self.assertTrue(period.changed_after_submission)

    def test_mark_and_unmark_paid(
        self,
    ):
        self._create_income('1000.00')

        response = self._generate()

        period_id = response.data['id']

        response = self.client.post(
            reverse(
                'v1-tax-period-mark-paid',
                args=[period_id],
            ),
            {
                'paid_amount': '10.00',
                'comment': 'Paid',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        period = TaxPeriod.objects.get(id=period_id)

        self.assertEqual(
            period.payment_status,
            'paid',
        )

        self.assertEqual(
            period.paid_amount,
            Decimal('10.00'),
        )

        self.assertIsNotNone(period.paid_at)

        response = self.client.post(
            reverse(
                ('v1-tax-period-unmark-paid'),
                args=[period_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        period.refresh_from_db()

        self.assertEqual(
            period.payment_status,
            'not_paid',
        )

        self.assertEqual(
            period.paid_amount,
            Decimal('0.00'),
        )

        self.assertIsNone(period.paid_at)

    def test_declaration_values(
        self,
    ):
        self._create_income('1350.00')

        response = self._generate()

        period_id = response.data['id']

        response = self.client.get(
            reverse(
                ('v1-tax-period-declaration-values'),
                args=[period_id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.data['data']

        self.assertEqual(
            data['field_17'],
            '1350.00',
        )

        self.assertEqual(
            data['field_20'],
            '1350.00',
        )

        self.assertEqual(
            data['field_26'],
            '13.50',
        )

    def test_filter_by_year_and_status(
        self,
    ):
        TaxPeriod.objects.create(
            user=self.user,
            year=2025,
            month=12,
            deadline='2026-01-15',
        )

        TaxPeriod.objects.create(
            user=self.user,
            year=2026,
            month=1,
            deadline='2026-02-15',
            declaration_status=('submitted'),
        )

        response = self.client.get(
            reverse('v1-tax-period-list'),
            {
                'year': 2026,
                'status': 'submitted',
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]['year'],
            2026,
        )
