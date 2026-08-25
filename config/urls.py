from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from config.views import HealthCheckAPIView

urlpatterns = [
    path(
        'admin/',
        admin.site.urls,
    ),
    path(
        'api/v1/health/',
        HealthCheckAPIView.as_view(),
        name='health',
    ),
    path(
        'api/v1/schema/',
        SpectacularAPIView.as_view(),
        name='schema',
    ),
    path(
        'api/v1/docs/',
        SpectacularSwaggerView.as_view(),
        name='swagger-ui',
    ),
    path(
        'api/v1/redoc/',
        SpectacularRedocView.as_view(),
        name='redoc',
    ),
    path(
        'api/',
        include('incomes.urls'),
    ),
    path(
        'api/reports/',
        include('incomes.report_urls'),
    ),
    path(
        'api/',
        include('invoices.urls'),
    ),
    path(
        'api/v1/auth/',
        include('accounts.urls'),
    ),
    path(
        'api/v1/auth/',
        include('accounts.urls'),
    ),
    path(
        'api/v1/',
        include('accounts.profile_urls'),
    ),
    path(
        'api/v1/',
        include('finances.urls'),
    ),
    path(
        'api/v1/',
        include('exchange_rates.urls'),
    ),
    path(
        'api/v1/',
        include('incomes.api_v1_urls'),
    ),
    path(
        'api/v1/reports/',
        include('incomes.api_v1_report_urls'),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
