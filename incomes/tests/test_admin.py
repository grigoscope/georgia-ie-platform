from decimal import Decimal

from django.contrib import admin
from django.test import (
    RequestFactory,
    TestCase,
)
from django.utils import timezone

from accounts.models import User
from exchange_rates.models import (
    Currency,
    ExchangeRate,
)
from finances.models import (
    Counterparty,
    FinancialAccount,
)
from incomes.admin import (
    IncomeEntryAdmin,
    IncomeEntryAdminForm,
)
from incomes.models import IncomeEntry


class IncomeAdminTests(TestCase):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                email='income-admin@example.com',
                password='Password123!',
            )
        )

        self.staff = (
            User.objects.create_user(
                email='staff@example.com',
                password='Password123!',
                is_staff=True,
            )
        )

        self.superuser = (
            User.objects.create_superuser(
                email='super@example.com',
                password='Password123!',
            )
        )

        self.currency = (
            Currency.objects.create(
                code='GEL',
                name='Georgian Lari',
                kind='fiat',
                decimal_places=2,
                is_active=True,
            )
        )

        self.account = (
            FinancialAccount
            .objects
            .create(
                user=self.user,
                name='Main GEL',
                type='bank_account',
                default_currency=
                    self.currency,
                default_declaration_category=
                    'cashless_20',
                is_active=True,
            )
        )

        self.income = (
            IncomeEntry.objects.create(
                user=self.user,
                received_at=timezone.now(),
                description='Admin test income',
                financial_account=
                    self.account,
                payment_method=
                    'bank_transfer',
                original_amount=
                    Decimal('100.00'),
                original_currency=
                    self.currency,
                exchange_rate_value=
                    Decimal('1'),
                exchange_rate_unit=1,
                exchange_rate_source=
                    'GEL',
                exchange_rate_date=
                    timezone.localdate(),
                amount_gel=
                    Decimal('100.00'),
                declaration_category=
                    'cashless_20',
                vat_amount=
                    Decimal('0.00'),
            )
        )

        self.factory = (
            RequestFactory()
        )

        self.model_admin = (
            IncomeEntryAdmin(
                IncomeEntry,
                admin.site,
            )
        )

    def form_data(
        self,
        *,
        amount_gel='100.00',
        category='cashless_20',
        reason='',
    ):
        return {
            'user': str(
                self.user.pk,
            ),
            'received_at':
                self.income
                .received_at
                .strftime(
                    '%Y-%m-%d %H:%M:%S',
                ),
            'description':
                self.income.description,
            'additional_info': '',
            'counterparty': '',
            'financial_account': str(
                self.account.pk,
            ),
            'payment_method':
                self.income
                .payment_method,
            'document_number': '',
            'document_date': '',
            'invoice': '',
            'original_amount':
                str(
                    self.income
                    .original_amount,
                ),
            'original_currency':
                str(
                    self.currency.pk,
                ),
            'exchange_rate_value':
                '1',
            'exchange_rate_unit':
                '1',
            'exchange_rate_source':
                'GEL',
            'exchange_rate_date':
                self.income
                .exchange_rate_date
                .isoformat(),
            'exchange_rate_time': '',
            'amount_gel':
                amount_gel,
            'declaration_category':
                category,
            'vat_amount': '0.00',
            'comment': '',
            'crypto_asset': '',
            'crypto_network': '',
            'crypto_wallet_address': '',
            'crypto_tx_hash': '',
            'is_deleted': '',
            'change_reason': reason,
        }

    def test_admin_models_are_registered(
        self,
    ):
        self.assertIn(
            IncomeEntry,
            admin.site._registry,
        )

        self.assertIn(
            FinancialAccount,
            admin.site._registry,
        )

        self.assertIn(
            Counterparty,
            admin.site._registry,
        )

        self.assertIn(
            Currency,
            admin.site._registry,
        )

        self.assertIn(
            ExchangeRate,
            admin.site._registry,
        )

    def test_reason_is_required_for_gel_change(
        self,
    ):
        form = IncomeEntryAdminForm(
            data=self.form_data(
                amount_gel='110.00',
            ),
            instance=self.income,
        )

        self.assertFalse(
            form.is_valid(),
        )

        self.assertIn(
            'change_reason',
            form.errors,
        )

    def test_reason_allows_gel_change(
        self,
    ):
        form = IncomeEntryAdminForm(
            data=self.form_data(
                amount_gel='110.00',
                reason=(
                    'Исправление ошибочного '
                    'GEL-эквивалента'
                ),
            ),
            instance=self.income,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_reason_is_required_for_category_change(
        self,
    ):
        form = IncomeEntryAdminForm(
            data=self.form_data(
                category='other_21',
            ),
            instance=self.income,
        )

        self.assertFalse(
            form.is_valid(),
        )

        self.assertIn(
            'change_reason',
            form.errors,
        )

    def test_sensitive_fields_are_readonly_for_regular_staff(
        self,
    ):
        request = (
            self.factory.get(
                '/admin/incomes/incomeentry/',
            )
        )

        request.user = self.staff

        readonly = (
            self.model_admin
            .get_readonly_fields(
                request,
                self.income,
            )
        )

        self.assertIn(
            'amount_gel',
            readonly,
        )

        self.assertIn(
            'declaration_category',
            readonly,
        )

    def test_superuser_can_edit_sensitive_fields(
        self,
    ):
        request = (
            self.factory.get(
                '/admin/incomes/incomeentry/',
            )
        )

        request.user = (
            self.superuser
        )

        readonly = (
            self.model_admin
            .get_readonly_fields(
                request,
                self.income,
            )
        )

        self.assertNotIn(
            'amount_gel',
            readonly,
        )

        self.assertNotIn(
            'declaration_category',
            readonly,
        )
