class IncomeCategoryService:
    """Определение рекомендуемой графы декларации."""

    ACCOUNT_TYPE_MAPPING = {
        'cash_register': 'cash_register_18',
        'physical_pos': 'physical_pos_19',

        'bank_account': 'cashless_20',
        'bank_card': 'cashless_20',
        'payment_system': 'cashless_20',

        'crypto_wallet': 'other_21',
        'other': 'other_21',
    }

    @classmethod
    def suggest(cls, financial_account):
        if financial_account.default_declaration_category:
            return financial_account.default_declaration_category

        return cls.ACCOUNT_TYPE_MAPPING.get(
            financial_account.type,
            'other_21',
        )