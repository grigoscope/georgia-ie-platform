from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from config.schema_urls import (
    urlpatterns as schema_urlpatterns,
)

urlpatterns = [
    path(
        'admin/',
        admin.site.urls,
    ),
    path(
        'api/v1/schema/',
        SpectacularAPIView.as_view(
            patterns=schema_urlpatterns,
        ),
        name='schema',
    ),
    path(
        'api/v1/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/v1/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
    path(
        'api/v1/',
        include('config.api_v1_urls'),
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
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
