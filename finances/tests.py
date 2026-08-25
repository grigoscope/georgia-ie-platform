from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from exchange_rates.models import Currency
from finances.models import (
    Counterparty,
    FinancialAccount,
)

User = get_user_model()


class FinancesAPITests(APITestCase):
    """API счетов и контрагентов."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
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

        self.usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            kind='fiat',
            decimal_places=2,
        )

        self.client.force_authenticate(user=self.user)

    def test_accounts_require_authentication(
        self,
    ):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse('account-list'))

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_create_account(self):
        response = self.client.post(
            reverse('account-list'),
            {
                'name': 'TBC USD',
                'type': 'bank_account',
                'default_currency': (self.usd.id),
                'provider_name': 'TBC Bank',
                'use_in_invoices': True,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        account = FinancialAccount.objects.get()

        self.assertEqual(
            account.user,
            self.user,
        )

    def test_foreign_account_is_hidden(
        self,
    ):
        account = FinancialAccount.objects.create(
            user=self.other_user,
            name='Foreign',
            type='bank_account',
            default_currency=self.gel,
        )

        response = self.client.get(
            reverse(
                'account-detail',
                args=[account.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_set_default_account(self):
        first = FinancialAccount.objects.create(
            user=self.user,
            name='First',
            type='bank_account',
            default_currency=self.gel,
            is_default=True,
        )

        second = FinancialAccount.objects.create(
            user=self.user,
            name='Second',
            type='bank_account',
            default_currency=self.usd,
        )

        response = self.client.post(
            reverse(
                'account-set-default',
                args=[second.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertFalse(first.is_default)

        self.assertTrue(second.is_default)

    def test_archive_account(self):
        account = FinancialAccount.objects.create(
            user=self.user,
            name='Account',
            type='bank_account',
            default_currency=self.gel,
            is_default=True,
            use_in_invoices=True,
        )

        response = self.client.post(
            reverse(
                'account-archive',
                args=[account.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        account.refresh_from_db()

        self.assertFalse(account.is_active)

        self.assertFalse(account.is_default)

        self.assertFalse(account.use_in_invoices)

    def test_account_filters(self):
        FinancialAccount.objects.create(
            user=self.user,
            name='GEL',
            type='cash',
            default_currency=self.gel,
        )

        FinancialAccount.objects.create(
            user=self.user,
            name='USD',
            type='bank_account',
            default_currency=self.usd,
        )

        response = self.client.get(
            reverse('account-list'),
            {
                'currency': 'USD',
                'type': 'bank_account',
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
            response.data[0]['name'],
            'USD',
        )

    def test_create_counterparty(self):
        response = self.client.post(
            reverse('counterparty-list'),
            {
                'name': 'Client LLC',
                'type': 'company',
                'country': 'Georgia',
                'email': ('client@example.com'),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        counterparty = Counterparty.objects.get()

        self.assertEqual(
            counterparty.user,
            self.user,
        )

    def test_foreign_counterparty_is_hidden(
        self,
    ):
        counterparty = Counterparty.objects.create(
            user=self.other_user,
            name='Foreign Client',
            type='company',
        )

        response = self.client.get(
            reverse(
                'counterparty-detail',
                args=[counterparty.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_counterparty_search(self):
        Counterparty.objects.create(
            user=self.user,
            name='Alpha LLC',
            type='company',
            country='Georgia',
        )

        Counterparty.objects.create(
            user=self.user,
            name='Beta LLC',
            type='company',
            country='Georgia',
        )

        response = self.client.get(
            reverse('counterparty-list'),
            {
                'search': 'Alpha',
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
            response.data['results'][0]['name'],
            'Alpha LLC',
        )

    def test_counterparty_pagination(
        self,
    ):
        for number in range(25):
            Counterparty.objects.create(
                user=self.user,
                name=f'Client {number}',
                type='individual',
            )

        response = self.client.get(reverse('counterparty-list'))

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
