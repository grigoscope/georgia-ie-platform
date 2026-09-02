import csv
import io
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from exchange_rates.models import Currency
from finances.models import FinancialAccount
from incomes.models import IncomeEntry

User = get_user_model()


class IncomeCSVExportAPITests(APITestCase):
    """Тесты CSV-экспорта доходов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpassword123',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpassword123',
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

        self.url = reverse('income-export-csv')

    def _create_income(
        self,
        *,
        user=None,
        account=None,
        description='Разработка сайта',
        is_deleted=False,
    ):
        user = user or self.user
        account = account or self.account

        received_at = timezone.make_aware(
            datetime(
                2026,
                8,
                21,
                12,
                0,
            )
        )

        return IncomeEntry.objects.create(
            user=user,
            received_at=received_at,
            description=description,
            financial_account=account,
            original_amount=Decimal('500.00'),
            original_currency=self.usd,
            exchange_rate_value=Decimal('2.7000000000'),
            exchange_rate_unit=1,
            exchange_rate_source='manual',
            exchange_rate_date=received_at.date(),
            amount_gel=Decimal('1350.00'),
            declaration_category='cashless_20',
            vat_amount=Decimal('0.00'),
            is_deleted=is_deleted,
        )

    def test_export_csv(self):
        self._create_income()

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response['Content-Type'],
            'text/csv; charset=utf-8',
        )

        text = response.content.decode('utf-8-sig')

        rows = list(
            csv.reader(
                io.StringIO(text),
                delimiter=';',
            )
        )

        self.assertEqual(
            rows[0][0],
            'date',
        )

        self.assertEqual(
            rows[1][1],
            'Разработка сайта',
        )

        self.assertEqual(
            rows[1][6],
            'USD',
        )

        self.assertEqual(
            rows[1][10],
            '1350.00',
        )

        self.assertEqual(
            rows[1][11],
            'cashless_20',
        )

    def test_export_ignores_deleted_and_foreign_incomes(self):
        self._create_income(
            description='Мой доход',
        )

        self._create_income(
            description='Удалённый доход',
            is_deleted=True,
        )

        self._create_income(
            user=self.other_user,
            account=self.other_account,
            description='Чужой доход',
        )

        response = self.client.get(self.url)

        text = response.content.decode('utf-8-sig')

        self.assertIn(
            'Мой доход',
            text,
        )

        self.assertNotIn(
            'Удалённый доход',
            text,
        )

        self.assertNotIn(
            'Чужой доход',
            text,
        )

    def test_export_filters_by_period(self):
        self._create_income(
            description='Август',
        )

        received_at = timezone.make_aware(
            datetime(
                2026,
                7,
                10,
                12,
                0,
            )
        )

        IncomeEntry.objects.create(
            user=self.user,
            received_at=received_at,
            description='Июль',
            financial_account=self.account,
            original_amount=Decimal('100'),
            original_currency=self.usd,
            exchange_rate_value=Decimal('2.7'),
            exchange_rate_unit=1,
            exchange_rate_source='manual',
            exchange_rate_date=received_at.date(),
            amount_gel=Decimal('270'),
            declaration_category='cashless_20',
        )

        response = self.client.get(
            self.url,
            {
                'year': 2026,
                'month': 8,
            },
        )

        text = response.content.decode('utf-8-sig')

        self.assertIn(
            'Август',
            text,
        )

        self.assertNotIn(
            'Июль',
            text,
        )

    def test_export_uses_tbilisi_month_boundary(
        self,
    ):
        received_at = datetime(
            2026,
            8,
            31,
            21,
            30,
            tzinfo=ZoneInfo('UTC'),
        )

        IncomeEntry.objects.create(
            user=self.user,
            received_at=received_at,
            description='September boundary',
            financial_account=self.account,
            original_amount=Decimal('100.00'),
            original_currency=self.usd,
            exchange_rate_value=Decimal('2.7000000000'),
            exchange_rate_unit=1,
            exchange_rate_source='manual',
            exchange_rate_date=(received_at.date()),
            amount_gel=Decimal('270.00'),
            declaration_category=('cashless_20'),
        )

        august_response = self.client.get(
            self.url,
            {
                'year': 2026,
                'month': 8,
            },
        )

        august_text = august_response.content.decode('utf-8-sig')

        self.assertNotIn(
            'September boundary',
            august_text,
        )

        september_response = self.client.get(
            self.url,
            {
                'year': 2026,
                'month': 9,
            },
        )

        september_text = september_response.content.decode('utf-8-sig')

        self.assertIn(
            'September boundary',
            september_text,
        )

        self.assertIn(
            '2026-09-01',
            september_text,
        )

    def test_export_filters_by_search(self):
        self._create_income(
            description='Оплата за занятие',
        )

        self._create_income(
            description='Разработка сайта',
        )

        response = self.client.get(
            self.url,
            {
                'search': 'занятие',
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        text = response.content.decode(
            'utf-8-sig'
        )

        self.assertIn(
            'Оплата за занятие',
            text,
        )

        self.assertNotIn(
            'Разработка сайта',
            text,
        )