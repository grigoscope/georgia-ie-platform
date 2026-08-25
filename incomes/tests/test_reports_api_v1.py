from datetime import datetime
from decimal import Decimal
from io import BytesIO
from zoneinfo import ZoneInfo

from django.contrib.auth import (
    get_user_model,
)
from django.urls import reverse
from openpyxl import load_workbook
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

from accounts.models import (
    EntrepreneurProfile,
)
from exchange_rates.models import Currency
from finances.models import (
    FinancialAccount,
)
from incomes.models import IncomeEntry

User = get_user_model()


class ReportsV1APITests(APITestCase):
    """Stage 4 API отчётов."""

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
        *,
        amount,
        category,
        received_at,
    ):
        local_date = received_at.astimezone(ZoneInfo('Asia/Tbilisi')).date()

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
            exchange_rate_date=local_date,
            amount_gel=Decimal(amount),
            declaration_category=category,
        )

    def test_reports_require_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse('v1-report-dashboard'))

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_monthly_report(self):
        self._create_income(
            amount='100.00',
            category='cashless_20',
            received_at=datetime(
                2026,
                8,
                10,
                12,
                tzinfo=ZoneInfo('Asia/Tbilisi'),
            ),
        )

        self._create_income(
            amount='50.00',
            category='other_21',
            received_at=datetime(
                2026,
                8,
                11,
                12,
                tzinfo=ZoneInfo('Asia/Tbilisi'),
            ),
        )

        response = self.client.get(
            reverse('v1-report-monthly'),
            {
                'year': 2026,
                'month': 8,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['year'],
            2026,
        )

        self.assertEqual(
            response.data['month'],
            8,
        )

        self.assertEqual(
            response.data['total_gel'],
            Decimal('150.00'),
        )

        self.assertEqual(
            response.data['count'],
            2,
        )

    def test_declaration_categories_report(
        self,
    ):
        self._create_income(
            amount='100.00',
            category='cashless_20',
            received_at=datetime(
                2026,
                8,
                10,
                12,
                tzinfo=ZoneInfo('Asia/Tbilisi'),
            ),
        )

        response = self.client.get(
            reverse(('v1-report-declaration-categories')),
            {
                'year': 2026,
                'month': 8,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        rows = {row['category']: row for row in response.data}

        self.assertEqual(
            rows['cashless_20']['total_gel'],
            Decimal('100.00'),
        )

        self.assertEqual(
            rows['other_21']['total_gel'],
            Decimal('0.00'),
        )

    def test_yearly_report(self):
        self._create_income(
            amount='100.00',
            category='cashless_20',
            received_at=datetime(
                2026,
                7,
                10,
                12,
                tzinfo=ZoneInfo('Asia/Tbilisi'),
            ),
        )

        self._create_income(
            amount='200.00',
            category='cashless_20',
            received_at=datetime(
                2026,
                8,
                10,
                12,
                tzinfo=ZoneInfo('Asia/Tbilisi'),
            ),
        )

        response = self.client.get(
            reverse('v1-report-yearly'),
            {
                'year': 2026,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['total_gel'],
            Decimal('300.00'),
        )

        self.assertEqual(
            response.data['count'],
            2,
        )

    def test_xlsx_export(self):
        self._create_income(
            amount='310.00',
            category='cashless_20',
            received_at=datetime(
                2026,
                8,
                25,
                12,
                tzinfo=ZoneInfo('Asia/Tbilisi'),
            ),
        )

        response = self.client.get(
            reverse('v1-income-export-xlsx'),
            {
                'year': 2026,
                'month': 8,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response['Content-Type'],
            ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        )

        self.assertTrue(response.content.startswith(b'PK'))

        workbook = load_workbook(BytesIO(response.content))

        worksheet = workbook['Incomes']

        self.assertEqual(
            worksheet['A1'].value,
            'date',
        )

        self.assertEqual(
            worksheet['B2'].value,
            'Test income',
        )

        self.assertEqual(
            Decimal(str(worksheet['K2'].value)),
            Decimal('310'),
        )

    def test_xlsx_export_requires_auth(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse('v1-income-export-xlsx'))

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
