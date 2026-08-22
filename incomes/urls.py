from django.urls import path
from rest_framework.routers import DefaultRouter

from incomes.export_views import IncomeCSVExportAPIView
from incomes.views import IncomeEntryViewSet


router = DefaultRouter()

router.register(
    'incomes',
    IncomeEntryViewSet,
    basename='income',
)


urlpatterns = [
    path(
        'incomes/export/csv/',
        IncomeCSVExportAPIView.as_view(),
        name='income-export-csv',
    ),
]

urlpatterns += router.urls