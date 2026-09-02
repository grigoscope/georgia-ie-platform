from django.core.management.base import (
    BaseCommand,
)

from exchange_rates.models import Currency


CURRENCIES = [
    ('GEL', 'Грузинский лари', 'fiat', 2),
    ('USD', 'Доллар США', 'fiat', 2),
    ('EUR', 'Евро', 'fiat', 2),
    ('GBP', 'Фунт стерлингов', 'fiat', 2),
    ('RUB', 'Российский рубль', 'fiat', 2),
    ('TRY', 'Турецкая лира', 'fiat', 2),
    ('CHF', 'Швейцарский франк', 'fiat', 2),
    ('CNY', 'Китайский юань', 'fiat', 2),
    ('JPY', 'Японская иена', 'fiat', 2),
    ('AED', 'Дирхам ОАЭ', 'fiat', 2),
    ('AMD', 'Армянский драм', 'fiat', 2),
    ('AZN', 'Азербайджанский манат', 'fiat', 2),
    ('KZT', 'Казахстанский тенге', 'fiat', 2),
    ('UAH', 'Украинская гривна', 'fiat', 2),
    ('PLN', 'Польский злотый', 'fiat', 2),
    ('CAD', 'Канадский доллар', 'fiat', 2),
    ('AUD', 'Австралийский доллар', 'fiat', 2),
    ('NZD', 'Новозеландский доллар', 'fiat', 2),
    ('SEK', 'Шведская крона', 'fiat', 2),
    ('NOK', 'Норвежская крона', 'fiat', 2),
    ('DKK', 'Датская крона', 'fiat', 2),
    ('CZK', 'Чешская крона', 'fiat', 2),
    ('HUF', 'Венгерский форинт', 'fiat', 2),
    ('RON', 'Румынский лей', 'fiat', 2),
    ('BRL', 'Бразильский реал', 'fiat', 2),
    ('SGD', 'Сингапурский доллар', 'fiat', 2),
    ('HKD', 'Гонконгский доллар', 'fiat', 2),
    ('ILS', 'Израильский шекель', 'fiat', 2),
    ('INR', 'Индийская рупия', 'fiat', 2),
    ('KRW', 'Южнокорейская вона', 'fiat', 2),
    ('KWD', 'Кувейтский динар', 'fiat', 3),
    ('QAR', 'Катарский риал', 'fiat', 2),
    ('MDL', 'Молдавский лей', 'fiat', 2),
    ('BYN', 'Белорусский рубль', 'fiat', 2),
    ('KGS', 'Киргизский сом', 'fiat', 2),
    ('UZS', 'Узбекский сум', 'fiat', 2),
    ('USDT', 'Tether', 'crypto', 6),
    ('USDC', 'USD Coin', 'crypto', 6),
    ('BTC', 'Bitcoin', 'crypto', 8),
    ('ETH', 'Ethereum', 'crypto', 8),
]


class Command(BaseCommand):
    help = 'Создать или обновить справочник валют'

    def handle(
        self,
        *args,
        **options,
    ):
        created_count = 0
        updated_count = 0

        for (
            code,
            name,
            kind,
            decimal_places,
        ) in CURRENCIES:
            currency, created = (
                Currency.objects.update_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'kind': kind,
                        'decimal_places': (
                            decimal_places
                        ),
                        'is_active': True,
                    },
                )
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            self.stdout.write(
                f'{currency.code}: {currency.name}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    'Готово. '
                    f'Создано: {created_count}, '
                    f'обновлено: {updated_count}'
                )
            )
        )