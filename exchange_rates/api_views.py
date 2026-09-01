from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import (
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.openapi_parameters import (
    EXCHANGE_RATE_PARAMETERS,
)
from exchange_rates.models import Currency
from exchange_rates.serializers import (
    ConversionSerializer,
    CryptoEstimateSerializer,
    CurrencySerializer,
    ExchangeRateSerializer,
)
from exchange_rates.services import (
    ExchangeRateService,
    GELConversionService,
    NBGRateError,
)


class CurrencyListAPIView(APIView):
    """Список доступных валют."""

    serializer_class = CurrencySerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        currencies = Currency.objects.filter(is_active=True).order_by(
            'kind',
            'code',
        )

        serializer = CurrencySerializer(
            currencies,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ExchangeRateAPIView(APIView):
    """Получить курс валюты."""

    serializer_class = ExchangeRateSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        tags=['Currencies'],
        parameters=(EXCHANGE_RATE_PARAMETERS),
    )
    def get(self, request):
        currency_code = request.query_params.get('currency', '').strip().upper()

        rate_date = request.query_params.get('date')

        if not currency_code:
            return Response(
                {'currency': ['Необходимо указать валюту.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_value = None

        if rate_date:
            from rest_framework.fields import DateField

            field = DateField()

            try:
                date_value = field.to_internal_value(rate_date)

            except Exception:
                return Response(
                    {'date': [('Дата должна быть в формате YYYY-MM-DD.')]},
                    status=(status.HTTP_400_BAD_REQUEST),
                )

        service = ExchangeRateService()

        try:
            rate = service.get_rate(
                currency_code,
                rate_date=date_value,
                user=request.user,
            )

        except Currency.DoesNotExist:
            return Response(
                {'currency': [('Неизвестная или неактивная валюта.')]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except NBGRateError as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            )

        serializer = ExchangeRateSerializer(rate)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ConversionAPIView(APIView):
    """Конвертация валюты в GEL."""

    serializer_class = ConversionSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = ConversionSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        mode = data['mode']

        conversion_service = GELConversionService()

        kwargs = {
            'amount': data['amount'],
            'currency_code': (data['currency']),
            'user': request.user,
            'rate_date': data.get('date'),
        }

        if mode == ConversionSerializer.MODE_MANUAL:
            kwargs.update(
                {
                    'manual_rate_value': (data['rate_value']),
                    'manual_rate_unit': (
                        data.get(
                            'rate_unit',
                            1,
                        )
                    ),
                    'manual_source': (data['source']),
                }
            )

        elif mode == ConversionSerializer.MODE_READY_GEL:
            kwargs['ready_amount_gel'] = data['amount_gel']

        try:
            result = conversion_service.convert(**kwargs)

        except (
            ValueError,
            ObjectDoesNotExist,
        ) as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except NBGRateError as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            )

        return Response(
            {'data': (self._serialize_result(result))},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _serialize_result(result):
        return {
            'original_amount': (str(result['original_amount'])),
            'currency': (result['currency_code']),
            'rate_value': (str(result['rate_value'])),
            'rate_unit': (str(result['rate_unit'])),
            'amount_gel': (str(result['amount_gel'])),
            'source': result['source'],
            'rate_date': (result['rate_date'].isoformat() if result.get('rate_date') else None),
            'rate_time': (result['rate_time'].isoformat() if result.get('rate_time') else None),
            'is_manual': (result['is_manual']),
            'warnings': (
                result.get(
                    'warnings',
                    [],
                )
            ),
        }


class CryptoEstimateAPIView(APIView):
    """Ручная оценка криптовалюты."""

    serializer_class = CryptoEstimateSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = CryptoEstimateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        service = GELConversionService()

        kwargs = {
            'amount': data['amount'],
            'currency_code': (data['asset']),
            'user': request.user,
            'rate_date': (data['valued_at'].date()),
        }

        if data.get('rate') is not None:
            kwargs.update(
                {
                    'manual_rate_value': (data['rate']),
                    'manual_rate_unit': (
                        data.get(
                            'rate_unit',
                            1,
                        )
                    ),
                    'manual_source': (data['source']),
                }
            )

        else:
            kwargs['ready_amount_gel'] = data['amount_gel']

        try:
            result = service.convert(**kwargs)

        except (
            ValueError,
            ObjectDoesNotExist,
        ) as error:
            return Response(
                {
                    'detail': str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = ConversionAPIView._serialize_result(result)

        response_data['valued_at'] = data['valued_at'].isoformat()

        response_data['asset'] = data['asset']

        return Response(
            {
                'data': response_data,
            },
            status=status.HTTP_200_OK,
        )
