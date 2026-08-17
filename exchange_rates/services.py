from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from django.utils import timezone

import requests


class NBGRateError(Exception):
    '''Ошибка получения курса из NGB'''


class NBGExchangeRateClient:
    '''Клиент API NGB'''

    URL = 'https://services.nbg.gov.ge/rates/service.asmx'

    SOAP_ACTION = 'http://www.nbg.ge/GetCurrentRates'

    def get_current_rate(self, currency_code):
        currency_code = currency_code.upper()
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetCurrentRates xmlns="http://www.nbg.ge/">
                    <Currencies>{currency_code}</Currencies>
                </GetCurrentRates>
            </soap:Body>
        </soap:Envelope>
        """

        try:
            response = requests.post(
                self.URL,
                data=xml,
                headers={
                    'Content-Type': 'text/xml; charset=utf-8',
                    'SOAPAction': self.SOAP_ACTION,
                },
                timeout=10,
            )

            response.raise_for_status()

        except requests.RequestException as error:
            raise NBGRateError(
                'Не удалось получить курс валюты из NGB'
            ) from error

        return self._parse_response(
            response.text,
            currency_code,
        )

    def _parse_response(self, xml_text, currency_code):
        import xml.etree.ElementTree as ET

        namespaces = {
            'nbg': 'http://www.nbg.ge/',
        }

        root = ET.fromstring(xml_text)

        rate_element = root.find(
            './/nbg:CurrencyRate',
            namespaces,
        )

        if rate_element is None:
            raise NBGRateError(
                f'Курс {currency_code} не найден.'
            )

        code = rate_element.findtext(
            'nbg:Code',
            namespaces=namespaces,
        )

        quantity = rate_element.findtext(
            'nbg:Quantity',
            namespaces=namespaces,
        )

        rate = rate_element.findtext(
            'nbg:Rate',
            namespaces=namespaces,
        )

        date_text = rate_element.findtext(
            'nbg:Date',
            namespaces=namespaces,
        )

        if not all([code, quantity, rate, date_text]):
            raise NBGRateError(
                'NGB вернул неполные данные курса.'
            )

        rate_datetime = datetime.fromisoformat(
            date_text.replace('Z', '+00:00')
        )

        return {
            'currency_code': code,
            'rate_value': Decimal(rate),
            'rate_unit': int(quantity),
            'rate_date': rate_datetime.date(),
            'rate_time': rate_datetime.time(),
            'source': 'NBG',
        }


from .models import Currency, ExchangeRate


class ExchangeRateService:
    """Сервис получения и сохранения валютных курсов."""

    def __init__(self):
        self.nbg_client = NBGExchangeRateClient()

    def get_current_rate(self, currency_code, user=None):
        currency_code = currency_code.upper()

        currency = Currency.objects.get(
            code=currency_code,
            is_active=True,
        )

        # GEL всегда 1:1
        if currency_code == 'GEL':
            existing_rate = ExchangeRate.objects.filter(
                currency=currency,
                rate_date=timezone.localdate(),
                source='SYSTEM',
                is_manual=False,
            ).first()

            if existing_rate:
                return existing_rate

            return ExchangeRate.objects.create(
                currency=currency,
                rate_date=timezone.localdate(),
                rate_time=None,
                rate_value=Decimal('1'),
                rate_unit=1,
                source='SYSTEM',
                is_manual=False,
                raw_reference='GEL base currency',
                created_by=user,
            )

        rate_data = self.nbg_client.get_current_rate(
            currency_code
        )

        existing_rate = ExchangeRate.objects.filter(
            currency=currency,
            rate_date=rate_data['rate_date'],
            source='NBG',
            is_manual=False,
        ).order_by('-created_at').first()

        if existing_rate:
            return existing_rate

        return ExchangeRate.objects.create(
            currency=currency,
            rate_date=rate_data['rate_date'],
            rate_time=rate_data['rate_time'],
            rate_value=rate_data['rate_value'],
            rate_unit=rate_data['rate_unit'],
            source='NBG',
            is_manual=False,
            raw_reference='NBG GetCurrentRates',
            created_by=user,
        )

    def create_manual_rate(
        self,
        currency_code,
        rate_value,
        rate_unit=1,
        rate_date=None,
        source='manual',
        user=None,
        raw_reference='',
    ):
        """Создать ручной курс."""

        currency_code = currency_code.upper()

        currency = Currency.objects.get(
            code=currency_code,
            is_active=True,
        )

        rate_value = Decimal(str(rate_value))
        rate_unit = int(rate_unit)

        if rate_value <= 0:
            raise ValueError(
                'Курс должен быть больше нуля.'
            )

        if rate_unit <= 0:
            raise ValueError(
                'Количество единиц валюты должно быть больше нуля.'
            )

        if currency_code == 'GEL':
            if rate_value != Decimal('1') or rate_unit != 1:
                raise ValueError(
                    'Для GEL курс должен быть равен 1.'
                )

        if rate_date is None:
            rate_date = timezone.localdate()

        return ExchangeRate.objects.create(
            currency=currency,
            rate_date=rate_date,
            rate_time=None,
            rate_value=rate_value,
            rate_unit=rate_unit,
            source=source,
            is_manual=True,
            raw_reference=raw_reference,
            created_by=user,
        )


class GELConversionService:
    """Сервис конвертации валюты в GEL."""

    GEL_QUANT = Decimal('0.01')
    RATE_QUANT = Decimal('0.0000000001')

    def __init__(self):
        self.rate_service = ExchangeRateService()

    def convert(
        self,
        amount,
        currency_code,
        user=None,
        manual_rate_value=None,
        manual_rate_unit=1,
        manual_source='manual',
        ready_amount_gel=None,
        rate_date=None,
    ):
        amount = Decimal(str(amount))
        currency_code = currency_code.upper()

        if amount <= 0:
            raise ValueError(
                'Сумма должна быть больше нуля.'
            )

        currency = Currency.objects.get(
            code=currency_code,
            is_active=True,
        )

        # 1. GEL → GEL
        if currency_code == 'GEL':
            amount_gel = amount.quantize(
                self.GEL_QUANT,
                rounding=ROUND_HALF_UP,
            )

            return {
                'original_amount': amount,
                'currency_code': currency.code,
                'rate_value': Decimal('1'),
                'rate_unit': 1,
                'amount_gel': amount_gel,
                'source': 'GEL',
                'rate_date': rate_date or timezone.localdate(),
                'rate_time': None,
                'is_manual': False,
                'warnings': [],
            }

        # 2. Пользователь уже знает GEL-эквивалент
        if ready_amount_gel is not None:
            ready_amount_gel = Decimal(
                str(ready_amount_gel)
            )

            if ready_amount_gel <= 0:
                raise ValueError(
                    'GEL-эквивалент должен быть больше нуля.'
                )

            amount_gel = ready_amount_gel.quantize(
                self.GEL_QUANT,
                rounding=ROUND_HALF_UP,
            )

            effective_rate = (
                amount_gel / amount
            ).quantize(
                self.RATE_QUANT,
                rounding=ROUND_HALF_UP,
            )

            return {
                'original_amount': amount,
                'currency_code': currency.code,
                'rate_value': effective_rate,
                'rate_unit': 1,
                'amount_gel': amount_gel,
                'source': 'provided_gel_equivalent',
                'rate_date': rate_date or timezone.localdate(),
                'rate_time': None,
                'is_manual': True,
                'warnings': [
                    'Использован готовый GEL-эквивалент.'
                ],
            }

        # 3. Явно задан ручной курс
        if manual_rate_value is not None:
            rate = self.rate_service.create_manual_rate(
                currency_code=currency_code,
                rate_value=manual_rate_value,
                rate_unit=manual_rate_unit,
                rate_date=rate_date,
                source=manual_source,
                user=user,
            )

        # 4. Крипта без ручной оценки запрещена
        elif currency.kind == 'crypto':
            raise ValueError(
                'Для криптовалюты необходимо указать '
                'ручной курс или готовый GEL-эквивалент.'
            )

        # 5. Фиат → NBG
        else:
            try:
                rate = self.rate_service.get_current_rate(
                    currency_code,
                    user=user,
                )

            except NBGRateError as error:
                raise NBGRateError(
                    'Не удалось получить автоматический курс. '
                    'Укажите ручной курс.'
                ) from error

        amount_gel = (
            amount
            / Decimal(rate.rate_unit)
            * rate.rate_value
        )

        amount_gel = amount_gel.quantize(
            self.GEL_QUANT,
            rounding=ROUND_HALF_UP,
        )

        warnings = []

        if rate.is_manual:
            warnings.append(
                'Использован ручной курс.'
            )

        return {
            'original_amount': amount,
            'currency_code': currency.code,
            'rate_value': rate.rate_value,
            'rate_unit': rate.rate_unit,
            'amount_gel': amount_gel,
            'source': rate.source,
            'rate_date': rate.rate_date,
            'rate_time': rate.rate_time,
            'is_manual': rate.is_manual,
            'warnings': warnings,
        }