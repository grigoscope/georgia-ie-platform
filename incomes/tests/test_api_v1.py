from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import (
    Counterparty,
    FinancialAccount,
)
from incomes.models import IncomeEntry

User = get_user_model()


class IncomeV1APITests(APITestCase):
    """Stage 4 API доходов."""

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

        self.other_account = FinancialAccount.objects.create(
            user=self.other_user,
            name='Other',
            type='bank_account',
            default_currency=self.gel,
        )

        self.counterparty = Counterparty.objects.create(
            user=self.user,
            name='Alpha Client',
            type='company',
            country='Georgia',
        )

        self.client.force_authenticate(user=self.user)

        self.list_url = reverse('v1-income-list')

    def _create_income(
        self,
        *,
        description,
        received_at,
        amount='100.00',
        category='cashless_20',
        counterparty=None,
    ):
        return IncomeEntry.objects.create(
            user=self.user,
            received_at=received_at,
            description=description,
            counterparty=counterparty,
            financial_account=self.account,
            original_amount=Decimal(amount),
            original_currency=self.gel,
            exchange_rate_value=Decimal('1'),
            exchange_rate_unit=1,
            exchange_rate_source='GEL',
            exchange_rate_date=(received_at.astimezone(ZoneInfo('Asia/Tbilisi')).date()),
            amount_gel=Decimal(amount),
            declaration_category=category,
        )

    def test_requires_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_list_is_paginated(self):
        for number in range(25):
            self._create_income(
                description=(f'Income {number}'),
                received_at=datetime(
                    2026,
                    8,
                    1,
                    12,
                    0,
                    tzinfo=ZoneInfo('Asia/Tbilisi'),
                ),
            )

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['count'],
            25,
        )

        self.assertEqual(
            len(response.data['results']),
            20,
        )

    def test_month_filter_uses_business_timezone(
        self,
    ):
        self._create_income(
            description='September',
            received_at=datetime(
                2026,
                8,
                31,
                21,
                30,
                tzinfo=ZoneInfo('UTC'),
            ),
        )

        august = self.client.get(
            self.list_url,
            {
                'year': 2026,
                'month': 8,
            },
        )

        september = self.client.get(
            self.list_url,
            {
                'year': 2026,
                'month': 9,
            },
        )

        self.assertEqual(
            august.data['count'],
            0,
        )

        self.assertEqual(
            september.data['count'],
            1,
        )

    def test_filters(self):
        self._create_income(
            description='Alpha project',
            received_at=datetime(
                2026,
                8,
                10,
                12,
                tzinfo=ZoneInfo('Asia/Tbilisi'),
            ),
            category='cashless_20',
            counterparty=self.counterparty,
        )

        self._create_income(
            description='Other project',
            received_at=datetime(
                2026,
                8,
                11,
                12,
                tzinfo=ZoneInfo('Asia/Tbilisi'),
            ),
            category='other_21',
        )

        response = self.client.get(
            self.list_url,
            {
                'search': 'Alpha',
                'declaration_category': ('cashless_20'),
                'counterparty': (self.counterparty.id),
                'currency': 'GEL',
                'account': (self.account.id),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['count'],
            1,
        )

        self.assertEqual(
            response.data['results'][0]['description'],
            'Alpha project',
        )

    def test_foreign_income_is_hidden(
        self,
    ):
        income = IncomeEntry.objects.create(
            user=self.other_user,
            received_at=datetime(
                2026,
                8,
                10,
                12,
                tzinfo=ZoneInfo('Asia/Tbilisi'),
            ),
            description='Foreign',
            financial_account=(self.other_account),
            original_amount=Decimal('100.00'),
            original_currency=self.gel,
            exchange_rate_value=Decimal('1'),
            exchange_rate_unit=1,
            exchange_rate_source='GEL',
            exchange_rate_date=(
                datetime(
                    2026,
                    8,
                    10,
                    tzinfo=ZoneInfo('Asia/Tbilisi'),
                ).date()
            ),
            amount_gel=Decimal('100.00'),
            declaration_category=('cashless_20'),
        )

        response = self.client.get(
            reverse(
                'v1-income-detail',
                args=[income.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_preview_does_not_create_income(
        self,
    ):
        response = self.client.post(
            reverse('v1-income-preview'),
            {
                'received_at': ('2026-08-25T12:00:00+04:00'),
                'financial_account': (self.account.id),
                'original_amount': ('310.00'),
                'original_currency': (self.gel.id),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['data']['amount_gel'],
            '310.00',
        )

        self.assertEqual(
            response.data['data']['suggested_category'],
            'cashless_20',
        )

        self.assertEqual(
            IncomeEntry.objects.count(),
            0,
        )

    def test_preview_rejects_foreign_account(
        self,
    ):
        response = self.client.post(
            reverse('v1-income-preview'),
            {
                'received_at': ('2026-08-25T12:00:00+04:00'),
                'financial_account': (self.other_account.id),
                'original_amount': ('310.00'),
                'original_currency': (self.gel.id),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_restore_income(self):
        create_response = self.client.post(
            self.list_url,
            {
                'received_at': ('2026-08-25T12:00:00+04:00'),
                'description': ('Restorable'),
                'financial_account': (self.account.id),
                'original_amount': ('100.00'),
                'original_currency': (self.gel.id),
                'declaration_category': ('cashless_20'),
            },
            format='json',
        )

        self.assertEqual(
            create_response.status_code,
            status.HTTP_201_CREATED,
        )

        income_id = create_response.data['id']

        delete_response = self.client.delete(
            reverse(
                'v1-income-detail',
                args=[income_id],
            )
        )

        self.assertEqual(
            delete_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        income = IncomeEntry.objects.get(id=income_id)

        self.assertTrue(income.is_deleted)

        restore_response = self.client.post(
            reverse(
                'v1-income-restore',
                args=[income_id],
            )
        )

        self.assertEqual(
            restore_response.status_code,
            status.HTTP_200_OK,
        )

        income.refresh_from_db()

        self.assertFalse(income.is_deleted)

        self.assertIsNone(income.deleted_at)
