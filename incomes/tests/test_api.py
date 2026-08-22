from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import EntrepreneurProfile
from audit.models import AuditLog
from exchange_rates.models import Currency
from finances.models import FinancialAccount
from incomes.models import IncomeEntry
from taxes.models import TaxPeriod

User = get_user_model()


class IncomeEntryAPITests(APITestCase):
    """Тесты API журнала доходов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            tin='123456789',
            tax_rate=Decimal('1.00'),
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.other_user,
            business_name='Other Business',
            tin='987654321',
            tax_rate=Decimal('1.00'),
        )

        self.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            kind='fiat',
            decimal_places=2,
        )

        self.account = FinancialAccount.objects.create(
            user=self.user,
            name='TBC USD',
            type='bank_account',
            default_currency=self.usd,
        )

        self.other_account = FinancialAccount.objects.create(
            user=self.other_user,
            name='Other Account',
            type='bank_account',
            default_currency=self.usd,
        )

        self.client.force_authenticate(user=self.user)

        self.list_url = reverse('income-list')

    def _income_payload(self):
        return {
            'received_at': '2026-08-21T12:00:00+03:00',
            'description': 'Разработка сайта',
            'financial_account': self.account.id,
            'original_amount': '500.00',
            'original_currency': self.usd.id,
            'declaration_category': 'cashless_20',
            'manual_rate_value': '2.7000000000',
            'manual_rate_unit': 1,
            'manual_source': 'test_manual',
            'tax_period_deadline': '2026-09-15',
        }

    def _create_other_income(self):
        received_at = timezone.make_aware(
            datetime(
                2026,
                8,
                10,
                12,
                0,
            )
        )

        return IncomeEntry.objects.create(
            user=self.other_user,
            received_at=received_at,
            description='Чужой доход',
            financial_account=self.other_account,
            original_amount=Decimal('100.00'),
            original_currency=self.usd,
            exchange_rate_value=Decimal('2.7000000000'),
            exchange_rate_unit=1,
            exchange_rate_source='manual',
            exchange_rate_date=date(2026, 8, 10),
            amount_gel=Decimal('270.00'),
            declaration_category='cashless_20',
        )

    def test_create_income(self):
        response = self.client.post(
            self.list_url,
            self._income_payload(),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

        income = IncomeEntry.objects.get()

        self.assertEqual(
            income.user,
            self.user,
        )

        self.assertEqual(
            income.original_amount,
            Decimal('500.00'),
        )

        self.assertEqual(
            income.amount_gel,
            Decimal('1350.00'),
        )

        self.assertEqual(
            income.declaration_category,
            'cashless_20',
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

        self.assertTrue(
            AuditLog.objects.filter(
                user=self.user,
                object_type='IncomeEntry',
                object_id=income.id,
                action='create',
            ).exists()
        )

    def test_list_returns_only_current_user_incomes(self):
        response = self.client.post(
            self.list_url,
            self._income_payload(),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self._create_other_income()

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]['description'],
            'Разработка сайта',
        )

    def test_user_cannot_access_other_user_income(self):
        other_income = self._create_other_income()

        url = reverse(
            'income-detail',
            args=[other_income.id],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_patch_changes_category_and_tax_period(self):
        response = self.client.post(
            self.list_url,
            self._income_payload(),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        income_id = response.data['id']

        url = reverse(
            'income-detail',
            args=[income_id],
        )

        response = self.client.patch(
            url,
            {
                'declaration_category': 'other_21',
                'description': 'Исправленный доход',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        income = IncomeEntry.objects.get(id=income_id)

        self.assertEqual(
            income.description,
            'Исправленный доход',
        )

        self.assertEqual(
            income.declaration_category,
            'other_21',
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            period.field_20,
            Decimal('0.00'),
        )

        self.assertEqual(
            period.field_21,
            Decimal('1350.00'),
        )

        self.assertTrue(
            AuditLog.objects.filter(
                object_type='IncomeEntry',
                object_id=income.id,
                action='update',
            ).exists()
        )

    def test_delete_is_soft_delete(self):
        response = self.client.post(
            self.list_url,
            self._income_payload(),
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        income_id = response.data['id']

        url = reverse(
            'income-detail',
            args=[income_id],
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        income = IncomeEntry.objects.get(id=income_id)

        self.assertTrue(income.is_deleted)

        self.assertIsNotNone(income.deleted_at)

        self.assertEqual(
            IncomeEntry.objects.count(),
            1,
        )

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            0,
        )

        period = TaxPeriod.objects.get(
            user=self.user,
            year=2026,
            month=8,
        )

        self.assertEqual(
            period.field_17,
            Decimal('0.00'),
        )

        self.assertEqual(
            period.field_20,
            Decimal('0.00'),
        )

        self.assertTrue(
            AuditLog.objects.filter(
                object_type='IncomeEntry',
                object_id=income.id,
                action='delete',
            ).exists()
        )

    def test_cannot_create_income_with_foreign_account(self):
        payload = self._income_payload()

        payload['financial_account'] = self.other_account.id

        response = self.client.post(
            self.list_url,
            payload,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            0,
        )
