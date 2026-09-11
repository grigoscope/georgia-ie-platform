from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import EntrepreneurProfile
from exchange_rates.models import Currency
from finances.models import FinancialAccount
from incomes.services import IncomeService

User = get_user_model()


class CryptoIncomeSnapshotTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='crypto-snapshot@example.com',
            password='testpassword123',
        )

        EntrepreneurProfile.objects.create(
            user=self.user,
            business_name='Crypto Test',
            tin='123456789',
            tax_rate=Decimal('1.00'),
        )

        self.usdt = Currency.objects.create(
            code='USDT',
            name='Tether',
            kind='crypto',
            decimal_places=6,
        )

        self.wallet = FinancialAccount.objects.create(
            user=self.user,
            name='USDT TRC20',
            type='crypto_wallet',
            default_currency=self.usdt,
            crypto_asset='USDT',
            crypto_network='TRC20',
            wallet_address='OLD_WALLET_ADDRESS',
            default_declaration_category='other_21',
        )

        self.other_wallet = FinancialAccount.objects.create(
            user=self.user,
            name='USDT ERC20',
            type='crypto_wallet',
            default_currency=self.usdt,
            crypto_asset='USDT',
            crypto_network='ERC20',
            wallet_address='SECOND_WALLET_ADDRESS',
            default_declaration_category='other_21',
        )

        self.received_at = timezone.make_aware(
            datetime(
                2026,
                9,
                11,
                12,
                0,
            )
        )

        self.service = IncomeService()

    def create_income(self):
        return self.service.create_income(
            user=self.user,
            received_at=self.received_at,
            description='Crypto payment',
            financial_account=self.wallet,
            original_amount=Decimal('1200'),
            original_currency=self.usdt,
            declaration_category='other_21',
            payment_method='crypto',
            crypto_tx_hash='tx-original',
            manual_rate_value=Decimal('2.60'),
            manual_rate_unit=1,
            manual_source='Binance',
        )

    def test_same_wallet_edit_preserves_crypto_snapshot(self):
        income = self.create_income()

        self.assertEqual(
            income.crypto_asset,
            'USDT',
        )
        self.assertEqual(
            income.crypto_network,
            'TRC20',
        )
        self.assertEqual(
            income.crypto_wallet_address,
            'OLD_WALLET_ADDRESS',
        )

        self.wallet.crypto_network = 'BEP20'
        self.wallet.wallet_address = 'NEW_WALLET_ADDRESS'
        self.wallet.save(
            update_fields=[
                'crypto_network',
                'wallet_address',
                'updated_at',
            ]
        )

        self.service.update_income(
            income=income,
            description='Edited crypto payment',
            crypto_tx_hash='tx-edited',
        )

        income.refresh_from_db()

        self.assertEqual(
            income.description,
            'Edited crypto payment',
        )
        self.assertEqual(
            income.crypto_tx_hash,
            'tx-edited',
        )
        self.assertEqual(
            income.crypto_asset,
            'USDT',
        )
        self.assertEqual(
            income.crypto_network,
            'TRC20',
        )
        self.assertEqual(
            income.crypto_wallet_address,
            'OLD_WALLET_ADDRESS',
        )

    def test_changing_wallet_refreshes_crypto_snapshot(self):
        income = self.create_income()

        self.service.update_income(
            income=income,
            financial_account=self.other_wallet,
            crypto_tx_hash='tx-second-wallet',
        )

        income.refresh_from_db()

        self.assertEqual(
            income.financial_account,
            self.other_wallet,
        )
        self.assertEqual(
            income.crypto_asset,
            'USDT',
        )
        self.assertEqual(
            income.crypto_network,
            'ERC20',
        )
        self.assertEqual(
            income.crypto_wallet_address,
            'SECOND_WALLET_ADDRESS',
        )
        self.assertEqual(
            income.crypto_tx_hash,
            'tx-second-wallet',
        )
