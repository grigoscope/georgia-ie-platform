from django.urls import path
from rest_framework.routers import DefaultRouter

from incomes.api_v1_views import (
    IncomeEntryV1ViewSet,
)
from incomes.export_views import (
    IncomeCSVExportAPIView,
)

router = DefaultRouter()

router.register(
    'incomes',
    IncomeEntryV1ViewSet,
    basename='v1-income',
)


urlpatterns = [
    path(
        'incomes/export.csv',
        IncomeCSVExportAPIView.as_view(),
        name='v1-income-export-csv',
    ),
]

urlpatterns += router.urls
