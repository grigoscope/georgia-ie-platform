from django.urls import path

from exchange_rates.api_views import (
    ConversionAPIView,
    CryptoEstimateAPIView,
    CurrencyListAPIView,
    ExchangeRateAPIView,
)

urlpatterns = [
    path(
        'currencies/',
        CurrencyListAPIView.as_view(),
        name='currency-list',
    ),
    path(
        'exchange-rates/',
        ExchangeRateAPIView.as_view(),
        name='exchange-rate',
    ),
    path(
        'exchange-rates/convert/',
        ConversionAPIView.as_view(),
        name='exchange-rate-convert',
    ),
    path(
        'exchange-rates/crypto-estimate/',
        CryptoEstimateAPIView.as_view(),
        name='exchange-rate-crypto-estimate',
    ),
]
